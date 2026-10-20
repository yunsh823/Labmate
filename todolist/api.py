"""Bridge exposed to the web UI as window.pywebview.api.

Every method returns JSON-serializable data. Names starting with "_" are
hidden from JavaScript.
"""

import threading
from dataclasses import asdict
from datetime import date

from . import autostart
from .db import BUCKETS, VIEWS, Store, Task
from .gcal import CalendarSync
from . import places
from .weather import Weather, latlon_to_grid

# Allowed values per setting; None means free text (validated separately).
SETTINGS = {
    "theme": ("system", "light", "dark"),
    "lang": ("ko", "en"),
    "sidebar": ("expanded", "collapsed"),
    "font": None,  # "" = app default, otherwise a system font family name
    "remind": ("off", "5", "10", "15", "30"),  # minutes before a timed task/event
}
DEFAULTS = {"theme": "system", "lang": "ko", "sidebar": "expanded", "font": "", "remind": "10"}


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
                "counts": {v: self._store.count(v, project, today) for v in VIEWS},
                "projects": self._store.projects(),
                "settings": {k: self._store.get_setting(k, v) for k, v in DEFAULTS.items()},
                "events": self._gcal.today_events if view == "today" else [],
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
        return {"has_client": g.has_client_file(), "connected": g.connected(), "account": g.account,
                "last_sync": g.last_sync, "error": g.error, "needs_reauth": g.needs_reauth}

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
