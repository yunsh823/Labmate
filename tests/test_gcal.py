import itertools
import sqlite3
import threading
from datetime import date, datetime, timedelta, timezone

import pytest

from labmate.db import Store
from labmate.gcal import APP_TAG, CalendarSync, event_body


class FakeCalendar:
    """In-memory stand-in for GoogleClient. `clock` drives event 'updated' stamps."""

    def __init__(self):
        self.events_by_id = {}
        self.other = []  # events on the user's calendars not created by the app
        self._ids = itertools.count(1)
        # Fake server clock runs ahead of the PC on purpose: sync must not rely on clocks agreeing.
        self.clock = datetime.now(timezone.utc) + timedelta(minutes=5)

    def tick(self, seconds=1):
        self.clock += timedelta(seconds=seconds)

    def _stamp(self, ev):
        self.tick()
        ev["updated"] = self.clock.isoformat()
        ev["etag"] = f"etag{next(self._ids)}"

    # GoogleClient interface
    def event_colors(self):
        return {"11": "#dc2127"}

    def calendars(self):
        return [{"id": "me@example.com", "primary": True, "summary": "me", "backgroundColor": "#4f6bed"}]

    def events(self, calendar_id, time_min, time_max):
        return list(self.other) + [e for e in self.events_by_id.values() if e.get("status") != "cancelled"]

    def app_events(self, updated_min):
        return [e for e in self.events_by_id.values()
                if updated_min is None or datetime.fromisoformat(e["updated"]) >= updated_min]

    def get(self, event_id):
        ev = self.events_by_id.get(event_id)
        return None if ev is None or ev.get("status") == "cancelled" else ev

    def insert(self, body):
        ev = {**body, "id": f"ev{next(self._ids)}", "status": "confirmed"}
        self._stamp(ev)
        self.events_by_id[ev["id"]] = ev
        return ev["id"], ev["etag"]

    def patch(self, event_id, body):
        if self.get(event_id) is None:
            return None
        self.events_by_id[event_id].update(body)
        self._stamp(self.events_by_id[event_id])
        return self.events_by_id[event_id]["etag"]

    def delete(self, event_id):
        if event_id in self.events_by_id:
            self.events_by_id[event_id]["status"] = "cancelled"
            self._stamp(self.events_by_id[event_id])

    # helpers for "the user edited the calendar"
    def user_moves(self, event_id, new_start: datetime, title=None):
        ev = self.events_by_id[event_id]
        ev["start"] = {"dateTime": new_start.isoformat()}
        ev["end"] = {"dateTime": (new_start + timedelta(hours=1)).isoformat()}
        if title:
            ev["summary"] = title
        self._stamp(ev)


TODAY = date.today()


@pytest.fixture
def env(tmp_path):
    store = Store(tmp_path / "t.db")
    sync = CalendarSync(store, threading.Lock())
    return store, sync, FakeCalendar()


def run(sync, cal):
    sync.sync(client=cal, now=datetime.now().astimezone())


def test_timed_task_creates_event_untimed_does_not(env):
    store, sync, cal = env
    timed = store.add("Lab meeting", due_date=TODAY, due_time="14:00")
    store.add("No time", due_date=TODAY)
    store.add("No date")
    run(sync, cal)
    assert len(cal.events_by_id) == 1
    ev = cal.events_by_id[store.get(timed).gcal_event_id]
    assert ev["summary"] == "Lab meeting"
    assert ev["extendedProperties"]["private"][APP_TAG] == "1"
    assert datetime.fromisoformat(ev["start"]["dateTime"]).strftime("%H:%M") == "14:00"


def test_second_sync_is_idempotent(env):
    store, sync, cal = env
    store.add("A", due_date=TODAY, due_time="09:00")
    run(sync, cal)
    stamps = {k: v["updated"] for k, v in cal.events_by_id.items()}
    run(sync, cal)
    assert {k: v["updated"] for k, v in cal.events_by_id.items()} == stamps


def test_local_edit_patches_event_and_keeps_duration(env):
    store, sync, cal = env
    tid = store.add("A", due_date=TODAY, due_time="09:00")
    run(sync, cal)
    eid = store.get(tid).gcal_event_id
    # user made it a 2h event in the calendar earlier
    start = datetime.fromisoformat(cal.events_by_id[eid]["start"]["dateTime"])
    cal.events_by_id[eid]["end"] = {"dateTime": (start + timedelta(hours=2)).isoformat()}
    store.update(tid, title="A (moved)", due_time="15:00")
    run(sync, cal)
    ev = cal.events_by_id[eid]
    s, e = (datetime.fromisoformat(ev[k]["dateTime"]) for k in ("start", "end"))
    assert ev["summary"] == "A (moved)" and s.strftime("%H:%M") == "15:00" and e - s == timedelta(hours=2)


def test_calendar_edit_flows_back_to_task(env):
    store, sync, cal = env
    tid = store.add("A", due_date=TODAY, due_time="09:00")
    run(sync, cal)
    eid = store.get(tid).gcal_event_id
    new_start = datetime.combine(TODAY + timedelta(days=2), datetime.min.time()).replace(hour=16).astimezone()
    cal.user_moves(eid, new_start, title="A renamed")
    run(sync, cal)
    t = store.get(tid)
    assert (t.title, t.due_date, t.due_time) == ("A renamed", TODAY + timedelta(days=2), "16:00")
    # pulling must not echo back as a local edit
    stamp = cal.events_by_id[eid]["updated"]
    run(sync, cal)
    assert cal.events_by_id[eid]["updated"] == stamp


def test_calendar_delete_trashes_task(env):
    store, sync, cal = env
    tid = store.add("A", due_date=TODAY, due_time="09:00")
    run(sync, cal)
    cal.delete(store.get(tid).gcal_event_id)
    run(sync, cal)
    t = store.get(tid)
    assert t.deleted_at is not None and t.gcal_event_id is None


def test_local_trash_deletes_event_and_restore_recreates(env):
    store, sync, cal = env
    tid = store.add("A", due_date=TODAY, due_time="09:00")
    run(sync, cal)
    eid = store.get(tid).gcal_event_id
    store.delete(tid)
    run(sync, cal)
    assert cal.events_by_id[eid]["status"] == "cancelled"
    assert store.get(tid).gcal_event_id is None
    store.restore(tid)
    run(sync, cal)
    assert store.get(tid).gcal_event_id not in (None, eid)


def test_completing_task_leaves_event_alone(env):
    store, sync, cal = env
    tid = store.add("A", due_date=TODAY, due_time="09:00")
    run(sync, cal)
    eid = store.get(tid).gcal_event_id
    store.set_done(tid, True)
    run(sync, cal)
    assert cal.events_by_id[eid]["status"] == "confirmed"
    assert cal.events_by_id[eid]["summary"] == "A"


def test_removing_date_deletes_event_removing_time_makes_all_day(env):
    store, sync, cal = env
    a = store.add("A", due_date=TODAY, due_time="09:00")
    b = store.add("B", due_date=TODAY, due_time="10:00")
    run(sync, cal)
    ea, eb = store.get(a).gcal_event_id, store.get(b).gcal_event_id
    store.update(a, due_date=None, due_time=None)
    store.update(b, due_time=None)
    run(sync, cal)
    assert cal.events_by_id[ea]["status"] == "cancelled" and store.get(a).gcal_event_id is None
    assert cal.events_by_id[eb]["start"] == {"date": TODAY.isoformat()}


def test_today_events_exclude_app_events(env):
    store, sync, cal = env
    store.add("Mine", due_date=TODAY, due_time="09:00")
    now = datetime.now().astimezone()
    cal.other.append({"id": "x", "status": "confirmed", "summary": "Seminar",
                      "start": {"dateTime": now.replace(hour=11, minute=0).isoformat()},
                      "end": {"dateTime": now.replace(hour=12, minute=0).isoformat()}})
    run(sync, cal)
    assert [e["title"] for e in sync.today_events] == ["Seminar"]
    assert sync.today_events[0]["start"] == "11:00"
    assert sync.account == "me@example.com"


def test_expired_sign_in_asks_for_reconnect(env):
    from google.auth.exceptions import RefreshError
    store, sync, cal = env

    def expired(updated_min):
        raise RefreshError("invalid_grant: Token has been expired or revoked.")
    cal.app_events = expired
    with pytest.raises(RefreshError):
        run(sync, cal)
    assert sync.needs_reauth and sync.error is None


def test_migrates_v1_database(tmp_path):
    path = tmp_path / "old.db"
    conn = sqlite3.connect(path)
    conn.executescript("""
        CREATE TABLE tasks (id INTEGER PRIMARY KEY, title TEXT NOT NULL, notes TEXT NOT NULL DEFAULT '',
            bucket TEXT NOT NULL DEFAULT 'today', project TEXT NOT NULL DEFAULT '', due_date TEXT, due_time TEXT,
            recurrence TEXT, done INTEGER NOT NULL DEFAULT 0, completed_at TEXT, deleted_at TEXT,
            created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
        INSERT INTO tasks (title, created_at, updated_at) VALUES ('old', '2026-01-01T00:00:00', '2026-01-01T00:00:00');
        PRAGMA user_version = 1;
    """)
    conn.close()
    t = Store(path).get(1)
    assert t.title == "old" and t.gcal_event_id is None


def test_week_events_cover_seven_days(env):
    store, sync, cal = env
    now = datetime.now().astimezone()
    later = (now + timedelta(days=3)).replace(hour=10, minute=0)
    cal.other += [
        {"id": "a", "status": "confirmed", "summary": "Ongoing",
         "start": {"dateTime": (now - timedelta(days=1)).isoformat()}, "end": {"dateTime": (now + timedelta(hours=1)).isoformat()}},
        {"id": "b", "status": "confirmed", "summary": "Later",
         "start": {"dateTime": later.isoformat()}, "end": {"dateTime": (later + timedelta(hours=1)).isoformat()}},
        {"id": "c", "status": "confirmed", "summary": "Deadline",
         "start": {"date": (TODAY + timedelta(days=2)).isoformat()}, "end": {"date": (TODAY + timedelta(days=3)).isoformat()}},
    ]
    run(sync, cal)
    assert [e["title"] for e in sync.week_events] == ["Ongoing", "Deadline", "Later"]
    assert [e["date"] for e in sync.week_events] == [(TODAY + timedelta(days=n)).isoformat() for n in (0, 2, 3)]
    assert [e["title"] for e in sync.today_events] == ["Ongoing"]


def test_event_colour_from_google(env):
    store, sync, cal = env
    now = datetime.now().astimezone()
    for eid, extra in (("plain", {}), ("red", {"colorId": "11"})):
        cal.other.append({"id": eid, "status": "confirmed", "summary": eid, **extra,
                          "start": {"dateTime": now.replace(hour=11, minute=0).isoformat()},
                          "end": {"dateTime": now.replace(hour=12, minute=0).isoformat()}})
    run(sync, cal)
    colours = {e["title"]: (e["color"], e["event_color"]) for e in sync.today_events}
    assert colours == {"plain": ("#4f6bed", None), "red": ("#4f6bed", "#dc2127")}
