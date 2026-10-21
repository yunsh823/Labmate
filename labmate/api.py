"""Bridge exposed to the web UI as window.pywebview.api.

Every method returns JSON-serializable data. Names starting with "_" are
hidden from JavaScript.
"""

import json
import sys
import threading
import webbrowser
from dataclasses import asdict
from datetime import date, datetime, timedelta

from . import __version__, autostart, updater
from .db import BUCKETS, VIEWS, Store, Task
from .gcal import CalendarSync
from . import papers, places
from .weather import Weather, latlon_to_grid

# Allowed values per setting; None means free text (validated separately).
SETTINGS = {
    "theme": ("system", "light", "dark"),
    "lang": ("ko", "en"),
    "sidebar": ("expanded", "collapsed"),
    "font": None,  # "" = app default, otherwise a system font family name
    "remind": ("off", "5", "10", "15", "30"),  # minutes before a timed task/event
    "papers_enabled": ("on", "off"),
    "papers_preprints": ("off", "on"),  # most people never read preprints, so off by default
    "update_auto": ("on", "off"),  # check GitHub for a new version once a day
}
DEFAULTS = {"theme": "system", "lang": "ko", "sidebar": "expanded", "font": "", "remind": "10",
            "papers_enabled": "on", "papers_preprints": "off", "update_auto": "on"}
NOTIFY_TEXT_MAX = 50
MAX_PAPER_ITEMS = 10  # per list: seed papers, keywords, journals
# Colours offered for calendars in Settings (Google Calendar's own palette); they only change this app's display.
CAL_COLORS = ("#d50000", "#f4511e", "#f6bf26", "#33b679", "#039be5", "#3f51b5", "#8e24aa", "#616161")


def _task_dict(t: Task) -> dict:
    d = asdict(t)
    d["due_date"] = t.due_date.isoformat() if t.due_date else None
    return d


class Api:
    def __init__(self, store: Store, shell=None):
        self._store = store
        self._shell = shell  # desktop.Desktop when running as the app; None in tests
        self._lock = threading.Lock()
        self._font_cache: list[str] | None = None
        self._gcal = CalendarSync(store, self._lock)
        self._weather = Weather()
        self._update_info: dict | None = None  # newer release found by the last check
        self._update_error: str | None = None
        self._update_checked: datetime | None = None

    def _open_today(self) -> int:
        with self._lock:
            return self._store.count("today")

    def _changed(self) -> None:
        if self._shell:
            self._shell.refresh_icon()
            self._shell.request_sync()

    def _reminder_items(self) -> tuple[list[Task], list[dict]]:
        with self._lock:
            return self._store.timed_tasks_on(date.today()), list(self._gcal.today_events)

    def app_info(self) -> dict:
        shell = self._shell
        return {"hotkey": shell.HOTKEY_LABEL if shell else "", "hotkey_ok": bool(shell and shell.hotkey_ok),
                "autostart_supported": autostart.supported(),
                "autostart": autostart.supported() and autostart.is_enabled()}

    def set_autostart(self, on: bool) -> dict:
        if autostart.supported():
            autostart.set_enabled(bool(on))
        return self.app_info()

    def _sync_calendar(self) -> None:
        """One calendar sync pass; errors are kept for the Settings page, not raised."""
        try:
            self._gcal.sync()
        except Exception:
            pass

    def state(self, view: str, project: str | None = None) -> dict:
        """Everything one render needs, in a single round trip."""
        weather = self._weather.data if self._weather_config() else None  # takes the lock itself
        with self._lock:
            today = date.today()
            project = project or None
            return {
                "today": today.isoformat(),
                "tasks": [_task_dict(t) for t in self._store.list_view(view, project, today)],
                "counts": {**{v: self._store.count(v, project, today) for v in VIEWS},
                           "papers": self._store.count_new_papers()},
                "projects": self._store.projects(),
                "settings": {k: self._store.get_setting(k, v) for k, v in DEFAULTS.items()},
                "events": self._colored({"today": self._gcal.today_events, "week": self._gcal.week_events}.get(view, [])),
                "gcal_reauth": self._gcal.needs_reauth,
                "weather": weather,
            }

    def _setting(self, key: str) -> str:
        with self._lock:
            return self._store.get_setting(key, DEFAULTS[key])

    def set_setting(self, key: str, value: str) -> None:
        allowed = SETTINGS[key]  # KeyError for unknown keys
        if allowed is None:
            if len(value) > 100 or any(c in value for c in '"\\;{}'):
                raise ValueError(value)
        elif value not in allowed:
            raise ValueError(value)
        with self._lock:
            self._store.set_setting(key, value)
        if key == "lang" and self._shell:
            self._shell.refresh_icon()  # tray tooltip follows the language

    def fonts(self) -> list[str]:
        """Font families installed on this system."""
        if self._font_cache is None:
            import tkinter
            import tkinter.font
            root = tkinter.Tk()
            root.withdraw()
            try:
                names = tkinter.font.families(root)
            finally:
                root.destroy()
            # "@Name" entries are vertical-writing variants on Windows.
            self._font_cache = sorted({n for n in names if not n.startswith("@")}, key=str.casefold)
        return self._font_cache

    def add(self, title: str, bucket: str = "today", project: str = "") -> int:
        with self._lock:
            task_id = self._store.add(title, bucket=bucket if bucket in BUCKETS else "today",
                                      project=project or "")
        self._changed()
        return task_id

    def update(self, task_id: int, fields: dict) -> None:
        # Empty form values from HTML inputs mean "unset".
        fields = {k: (v if v != "" else None) for k, v in fields.items()}
        for key in ("project", "notes"):
            if key in fields and fields[key] is None:
                fields[key] = ""
        if fields.get("due_date") is None and "due_date" in fields:
            fields["due_time"] = None  # a time without a date is meaningless
        with self._lock:
            self._store.update(task_id, **fields)
        self._changed()

    def set_done(self, task_id: int, done: bool) -> None:
        with self._lock:
            self._store.set_done(task_id, done)
        self._changed()

    def delete(self, task_id: int) -> None:
        with self._lock:
            self._store.delete(task_id)
        self._changed()

    def restore(self, task_id: int) -> None:
        with self._lock:
            self._store.restore(task_id)
        self._changed()

    def purge(self, task_id: int) -> None:
        with self._lock:
            self._store.purge(task_id)

    # --- window control (no-ops without a desktop shell) --------------------

    def show_main(self, task_id: int | None = None) -> None:
        if self._shell:
            self._shell.show_main(task_id)

    def hide_popup(self) -> None:
        if self._shell:
            self._shell.hide_popup()

    def popup_blurred(self) -> None:
        if self._shell:
            self._shell.popup_blurred()

    # --- paper alerts -------------------------------------------------------------
    # Lists live in the settings table as JSON; errors are short codes the page translates.

    def _json_setting_text(self, key: str) -> str:
        with self._lock:
            return self._store.get_setting(key, "")

    def _json_setting(self, key: str) -> list:
        with self._lock:
            return json.loads(self._store.get_setting(key, "[]"))

    def _set_json_setting(self, key: str, value: list) -> None:
        with self._lock:
            self._store.set_setting(key, json.dumps(value, ensure_ascii=False))

    def papers_settings(self) -> dict:
        with self._lock:
            get = self._store.get_setting
            info = {"enabled": get("papers_enabled", "on"), "preprints": get("papers_preprints", "off"),
                    "notify_text": get("papers_notify_text", ""), "last_fetch": get("papers_last_fetch", ""),
                    "error": get("papers_error", "")}
        return {**info, "seeds": self._json_setting("papers_seeds"), "keywords": self._json_setting("papers_keywords"),
                "journals": self._json_setting("papers_journals"), "notify_max": NOTIFY_TEXT_MAX}

    def set_papers_notify_text(self, text: str) -> dict:
        """Empty text means the default line ("새 논문이 도착했어요.")."""
        text = " ".join(text.split())
        if len(text) > NOTIFY_TEXT_MAX:
            raise ValueError("too_long")
        with self._lock:
            self._store.set_setting("papers_notify_text", text)
        return self.papers_settings()

    def _add_to_list(self, key: str, item, same) -> dict:
        items = self._json_setting(key)
        if not any(same(x) for x in items):
            if len(items) >= MAX_PAPER_ITEMS:
                raise ValueError("too_many")
            self._set_json_setting(key, items + [item])
        return self.papers_settings()

    def _remove_from_list(self, key: str, same) -> dict:
        self._set_json_setting(key, [x for x in self._json_setting(key) if not same(x)])
        return self.papers_settings()

    def add_paper_seed(self, text: str) -> dict:
        doi = papers.normalize_doi(text)
        if not doi:
            raise ValueError("bad_doi")
        try:
            title = papers.lookup_title(doi)
        except papers.PaperError as e:
            raise ValueError(e.code) from None
        return self._add_to_list("papers_seeds", {"doi": doi, "title": title}, lambda x: x["doi"].lower() == doi.lower())

    def remove_paper_seed(self, doi: str) -> dict:
        return self._remove_from_list("papers_seeds", lambda x: x["doi"] == doi)

    def add_paper_keyword(self, keyword: str) -> dict:
        keyword = " ".join(keyword.replace(",", " ").split())[:60]
        if not keyword:
            raise ValueError("empty")
        return self._add_to_list("papers_keywords", keyword, lambda x: x.lower() == keyword.lower())

    def remove_paper_keyword(self, keyword: str) -> dict:
        return self._remove_from_list("papers_keywords", lambda x: x == keyword)

    def search_journals(self, query: str) -> list[dict]:
        if not query.strip():
            return []
        try:
            return papers.search_journals(query.strip())
        except papers.PaperError:
            return []

    def add_paper_journal(self, journal_id: str, name: str) -> dict:
        return self._add_to_list("papers_journals", {"id": journal_id, "name": name}, lambda x: x["id"] == journal_id)

    def remove_paper_journal(self, journal_id: str) -> dict:
        return self._remove_from_list("papers_journals", lambda x: x["id"] == journal_id)

    def _paper_sources(self) -> tuple[list[str], list[str], list[dict]]:
        return ([s["doi"] for s in self._json_setting("papers_seeds")], self._json_setting("papers_keywords"),
                self._json_setting("papers_journals"))

    def _fetch_papers(self) -> tuple[int, str | None]:
        """Fetch today's papers. Returns (number added, error code)."""
        seeds, keywords, journals = self._paper_sources()
        if not (seeds or keywords or journals):
            return 0, None
        with self._lock:
            known = self._store.paper_keys()
            include_preprints = self._store.get_setting("papers_preprints", "off") == "on"
        found, error = papers.fetch(seeds, keywords, journals, known, include_preprints)
        with self._lock:
            added = self._store.add_papers(found)
            self._store.set_setting("papers_error", error or "")
            if added or not error:  # a total failure is retried later instead of skipping the day
                self._store.set_setting("papers_last_fetch", date.today().isoformat())
        return added, error

    def _papers_due(self) -> bool:
        with self._lock:
            enabled = self._store.get_setting("papers_enabled", "on") == "on"
            last = self._store.get_setting("papers_last_fetch", "")
        return enabled and last != date.today().isoformat() and any(self._paper_sources())

    def papers_list(self) -> dict:
        """Papers for the 논문 tab. Opening the tab counts as seeing the new ones."""
        with self._lock:
            items = self._store.list_papers()
            self._store.mark_papers_seen()
        settings = self.papers_settings()
        return {"papers": items, "last_fetch": settings["last_fetch"], "error": settings["error"],
                "has_sources": any(self._paper_sources())}

    def fetch_papers_now(self) -> dict:
        self._fetch_papers()
        return self.papers_list()

    def open_paper(self, key: str) -> None:
        with self._lock:
            url = self._store.get_paper(key)["url"]
        if url.startswith(("https://", "http://")):
            webbrowser.open(url)

    def save_paper(self, key: str) -> None:
        """Add "읽기: <title>" to Later, with the link in the notes."""
        with self._lock:
            p = self._store.get_paper(key)
            prefix = "읽기: " if self._store.get_setting("lang", "ko") == "ko" else "Read: "
            self._store.add((prefix + p["title"])[:200], bucket="later", notes=p["url"])
            self._store.set_paper_status(key, "saved")
        self._changed()

    def hide_paper(self, key: str) -> None:
        with self._lock:
            self._store.set_paper_status(key, "hidden")

    # --- weather (KMA API Hub) ----------------------------------------------------
    # The key is stored like other settings but never sent back to the page.

    def _weather_place(self) -> tuple[str, tuple[int, int] | None]:
        """Chosen neighbourhood name and its official KMA grid."""
        with self._lock:
            name = self._store.get_setting("weather_place", "")
            nx, ny = self._store.get_setting("weather_nx", ""), self._store.get_setting("weather_ny", "")
            lat, lon = self._store.get_setting("weather_lat", ""), self._store.get_setting("weather_lon", "")
        if nx and ny:
            return name, (int(nx), int(ny))
        if lat and lon:  # set by an earlier version as coordinates
            return name, latlon_to_grid(float(lat), float(lon))
        return name, None

    def _weather_config(self) -> tuple[str, tuple[int, int]] | None:
        with self._lock:
            key = self._store.get_setting("kma_key", "")
        grid = self._weather_place()[1]
        return (key, grid) if key and grid else None

    def _refresh_weather(self) -> None:
        config = self._weather_config()
        if config:
            self._weather.refresh(*config)

    def weather_settings(self) -> dict:
        with self._lock:
            has_key = bool(self._store.get_setting("kma_key", ""))
        name, grid = self._weather_place()
        return {
            "has_key": has_key, "place": name, "grid": grid,
            "updated": (self._weather.data or {}).get("updated"), "error": self._weather.error,
        }

    def search_places(self, query: str) -> dict:
        results, total = places.search(query)
        return {"results": results, "total": total}

    def set_weather_key(self, key: str) -> dict:
        key = key.strip()
        if not key or len(key) > 200 or any(c.isspace() for c in key):
            raise ValueError("bad key")
        with self._lock:
            self._store.set_setting("kma_key", key)
        self._refresh_weather()
        return self.weather_settings()

    def set_weather_place(self, place_id: int) -> dict:
        name, nx, ny = places.get(int(place_id))
        with self._lock:
            self._store.set_setting("weather_place", name)
            self._store.set_setting("weather_nx", str(nx))
            self._store.set_setting("weather_ny", str(ny))
        self._weather._daily = None  # the cached min/max belonged to the old place
        self._refresh_weather()
        return self.weather_settings()

    # --- Google Calendar -------------------------------------------------------

    def gcal_status(self) -> dict:
        g = self._gcal
        with self._lock:
            custom = self._cal_colors()
        return {"has_client": g.has_client_file(), "connected": g.connected(), "account": g.account,
                "last_sync": g.last_sync, "error": g.error, "needs_reauth": g.needs_reauth,
                "calendars": [{**c, "custom": custom.get(c["id"], "")} for c in g.calendars], "palette": CAL_COLORS}

    def _cal_colors(self) -> dict:
        """Calendar id -> colour picked in Settings. Caller holds the lock."""
        return json.loads(self._store.get_setting("cal_colors", "{}"))

    def _colored(self, events: list[dict]) -> list[dict]:
        """Events with the colours picked in Settings applied. Caller holds the lock."""
        custom = self._cal_colors()
        return [{**e, "color": custom.get(e.get("calendar_id"), e["color"])} for e in events]

    def set_calendar_color(self, calendar_id: str, color: str) -> dict:
        """color: one of CAL_COLORS, or "" to go back to the calendar's Google colour."""
        if color and color not in CAL_COLORS:
            raise ValueError(color)
        with self._lock:
            custom = self._cal_colors()
            if color:
                custom[calendar_id] = color
            else:
                custom.pop(calendar_id, None)
            self._store.set_setting("cal_colors", json.dumps(custom))
        if self._shell:
            self._shell.after_sync()
        return self.gcal_status()

    def gcal_import_client(self) -> dict:
        path = self._shell.pick_json_file() if self._shell else None
        if path:
            self._gcal.import_client_file(path)
        return self.gcal_status()

    def gcal_connect(self) -> dict:
        self._gcal.connect()
        self._sync_calendar()
        if self._shell:
            self._shell.after_sync()
        return self.gcal_status()

    def gcal_disconnect(self) -> dict:
        self._gcal.disconnect()
        return self.gcal_status()

    def gcal_sync_now(self) -> dict:
        self._sync_calendar()
        if self._shell:
            self._shell.after_sync()
        return self.gcal_status()

    # --- updates ---------------------------------------------------------------

    def _update_due(self) -> bool:
        """Automatic check: at start and then daily (30 min after a failure), unless turned off."""
        if self._setting("update_auto") != "on":
            return False
        if self._update_checked is None:
            return True
        wait = timedelta(minutes=30) if self._update_error else timedelta(days=1)
        return datetime.now() - self._update_checked >= wait

    def _check_update(self) -> dict | None:
        try:
            self._update_info = updater.latest()
            self._update_error = None
        except Exception:
            self._update_error = "network"
        self._update_checked = datetime.now()
        return self._update_info

    def update_status(self) -> dict:
        info, checked = self._update_info, self._update_checked
        return {"current": __version__, "latest": info["version"] if info else None,
                "checked": checked.strftime("%H:%M") if checked else None, "error": self._update_error,
                "auto": self._setting("update_auto"), "can_install": bool(getattr(sys, "frozen", False))}

    def check_update_now(self) -> dict:
        self._check_update()
        if self._shell:
            self._shell.refresh_icon()  # shows or hides the tray's update item
        return self.update_status()

    def install_update(self) -> dict:
        info = self._update_info
        if not info:
            raise ValueError("no_update")
        if not getattr(sys, "frozen", False):
            raise ValueError("dev")  # running from source: there is no installed copy to replace
        try:
            path = updater.download(info)
        except ValueError:
            raise ValueError("corrupt") from None
        except Exception:
            raise ValueError("network") from None
        updater.install(path)
        if self._shell:
            self._shell.quit_soon()  # the installer would end the app anyway; close cleanly first
        return self.update_status()
