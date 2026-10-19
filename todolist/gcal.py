"""Google Calendar integration.

Rules (agreed with the user):
- A task with a date and time is mirrored to the primary calendar as an event.
- Title/date/time edits made in the calendar flow back to the task.
- Deleting the event in the calendar moves the task to the trash.
- Moving a task to the trash deletes its event. Completing a task does not touch it.
- Events from the user's calendars are shown read-only in the Today view.
"""

import json
import shutil
import threading
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path

from .db import Store, Task, data_dir

SCOPES = [
    "https://www.googleapis.com/auth/calendar.readonly",  # list calendars and their events
    "https://www.googleapis.com/auth/calendar.events",    # create/update/delete our events
]
APP_TAG = "todolist"  # private extended property marking events this app created
DEFAULT_DURATION = timedelta(hours=1)


def client_path() -> Path:
    return data_dir() / "client_secret.json"


def token_path() -> Path:
    return data_dir() / "google_token.json"


# --- Google API wrapper (replaced by a fake in tests) ------------------------

class GoogleClient:
    def __init__(self, creds):
        from googleapiclient.discovery import build
        self._svc = build("calendar", "v3", credentials=creds, cache_discovery=False)

    def calendars(self) -> list[dict]:
        items = self._svc.calendarList().list(minAccessRole="reader").execute().get("items", [])
        return [c for c in items if c.get("selected")]

    def events(self, calendar_id: str, time_min: datetime, time_max: datetime) -> list[dict]:
        return self._svc.events().list(
            calendarId=calendar_id, timeMin=time_min.isoformat(), timeMax=time_max.isoformat(),
            singleEvents=True, orderBy="startTime", maxResults=250,
        ).execute().get("items", [])

    def app_events(self, updated_min: datetime | None) -> list[dict]:
        """Events this app created on the primary calendar, including deleted ones."""
        out, page = [], None
        while True:
            kwargs = dict(calendarId="primary", privateExtendedProperty=f"{APP_TAG}=1",
                          showDeleted=True, maxResults=250, pageToken=page)
            if updated_min:
                kwargs["updatedMin"] = updated_min.isoformat()
            resp = self._svc.events().list(**kwargs).execute()
            out += resp.get("items", [])
            page = resp.get("nextPageToken")
            if not page:
                return out

    def get(self, event_id: str) -> dict | None:
        from googleapiclient.errors import HttpError
        try:
            return self._svc.events().get(calendarId="primary", eventId=event_id).execute()
        except HttpError as e:
            if e.resp.status in (404, 410):
                return None
            raise

    def insert(self, body: dict) -> tuple[str, str]:
        ev = self._svc.events().insert(calendarId="primary", body=body).execute()
        return ev["id"], ev["etag"]

    def patch(self, event_id: str, body: dict) -> str | None:
        """New etag, or None if the event no longer exists."""
        from googleapiclient.errors import HttpError
        try:
            return self._svc.events().patch(calendarId="primary", eventId=event_id, body=body).execute()["etag"]
        except HttpError as e:
            if e.resp.status in (404, 410):
                return None
            raise

    def delete(self, event_id: str) -> None:
        from googleapiclient.errors import HttpError
        try:
            self._svc.events().delete(calendarId="primary", eventId=event_id).execute()
        except HttpError as e:
            if e.resp.status not in (404, 410):
                raise


# --- conversions ---------------------------------------------------------------

def _local(dt: datetime) -> datetime:
    """Naive local timestamps from the DB -> aware."""
    return dt.astimezone() if dt.tzinfo is None else dt


def _parse_rfc3339(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def event_body(t: Task, duration: timedelta = DEFAULT_DURATION) -> dict:
    if t.due_time:
        start = datetime.combine(t.due_date, time.fromisoformat(t.due_time)).astimezone()
        when = {"start": {"dateTime": start.isoformat()}, "end": {"dateTime": (start + duration).isoformat()}}
    else:  # a linked task whose time was removed becomes an all-day event
        when = {"start": {"date": t.due_date.isoformat()},
                "end": {"date": (t.due_date + timedelta(days=1)).isoformat()}}
    return {
        "summary": t.title,
        **when,
        "extendedProperties": {"private": {APP_TAG: "1", f"{APP_TAG}_task_id": str(t.id)}},
    }


def event_when(ev: dict) -> tuple[date, str | None]:
    start = ev["start"]
    if "dateTime" in start:
        dt = _parse_rfc3339(start["dateTime"]).astimezone()
        return dt.date(), dt.strftime("%H:%M")
    return date.fromisoformat(start["date"]), None


def event_duration(ev: dict) -> timedelta:
    if "dateTime" in ev.get("start", {}) and "dateTime" in ev.get("end", {}):
        d = _parse_rfc3339(ev["end"]["dateTime"]) - _parse_rfc3339(ev["start"]["dateTime"])
        if d > timedelta(0):
            return d
    return DEFAULT_DURATION


def display_event(ev: dict, cal: dict) -> dict:
    start, end = ev["start"], ev["end"]
    all_day = "date" in start
    return {
        "title": ev.get("summary", ""),
        "all_day": all_day,
        "start": None if all_day else _parse_rfc3339(start["dateTime"]).astimezone().strftime("%H:%M"),
        "end": None if all_day else _parse_rfc3339(end["dateTime"]).astimezone().strftime("%H:%M"),
        "calendar": cal.get("summary", ""),
        "color": cal.get("backgroundColor", ""),
    }


# --- sync ------------------------------------------------------------------------

class CalendarSync:
    def __init__(self, store: Store, lock: threading.Lock):
        self._store = store
        self._lock = lock
        self._client = None
        self._run_lock = threading.Lock()
        self.last_sync: str | None = None
        self.last_pull: datetime | None = None
        self.error: str | None = None
        self.needs_reauth = False  # sign-in expired/revoked; the user must connect again
        self.account: str | None = None
        self.today_events: list[dict] = []

    # --- connection -----------------------------------------------------------

    def has_client_file(self) -> bool:
        return client_path().exists()

    def import_client_file(self, src: str) -> None:
        data = json.loads(Path(src).read_text(encoding="utf-8"))
        if "installed" not in data:
            raise ValueError("not a desktop OAuth client file")
        shutil.copyfile(src, client_path())

    def connected(self) -> bool:
        return token_path().exists()

    def connect(self) -> None:
        """Browser sign-in; blocks until the user finishes or 3 minutes pass."""
        from google_auth_oauthlib.flow import InstalledAppFlow
        flow = InstalledAppFlow.from_client_secrets_file(str(client_path()), SCOPES)
        creds = flow.run_local_server(port=0, open_browser=True, timeout_seconds=180,
                                      success_message="ToDoList: Google Calendar connected. You can close this tab.")
        token_path().write_text(creds.to_json(), encoding="utf-8")
        self._client = None
        self.needs_reauth = False
        self.error = None

    def disconnect(self) -> None:
        token_path().unlink(missing_ok=True)
        with self._lock:
            self._store.unlink_all()
        self._client = None
        self.account = None
        self.today_events = []
        self.last_sync = self.last_pull = self.error = None
        self.needs_reauth = False

    def _get_client(self):
        if self._client is None:
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
            creds = Credentials.from_authorized_user_file(str(token_path()), SCOPES)
            if not creds.valid and creds.refresh_token:
                creds.refresh(Request())
                token_path().write_text(creds.to_json(), encoding="utf-8")
            self._client = GoogleClient(creds)
        return self._client

    # --- one sync pass --------------------------------------------------------

    def sync(self, client=None, now: datetime | None = None) -> None:
        """Push local changes, pull calendar changes, refresh today's events."""
        if client is None and not self.connected():
            return
        with self._run_lock:
            try:
                self._sync(client or self._get_client(), now or datetime.now().astimezone())
                self.error = None
            except Exception as e:  # network/auth problems surface in Settings
                from google.auth.exceptions import RefreshError
                if isinstance(e, RefreshError):
                    # Expired or revoked sign-in (every 7 days while the OAuth app is in testing).
                    self.needs_reauth = True
                    self._client = None
                    self.error = None
                else:
                    self.error = str(e) or type(e).__name__
                raise

    def _sync(self, cal, now: datetime) -> None:
        pull_started = now
        # Overlap the window a little to tolerate clock skew; re-reading an event is harmless.
        since = self.last_pull - timedelta(minutes=2) if self.last_pull else None
        remote = {ev["id"]: ev for ev in cal.app_events(since)}

        with self._lock:
            tasks = self._store.calendar_candidates()

        for t in tasks:
            ev = remote.get(t.gcal_event_id) if t.gcal_event_id else None
            synced = _local(datetime.fromisoformat(t.gcal_synced_at)) if t.gcal_synced_at else None
            local_dirty = synced is None or _local(datetime.fromisoformat(t.updated_at)) > synced

            # Local trash -> delete the event.
            if t.deleted_at:
                cal.delete(t.gcal_event_id)
                with self._lock:
                    self._store.link_event(t.id, None)
                continue

            # Not linked yet -> create.
            if not t.gcal_event_id:
                event_id, etag = cal.insert(event_body(t))
                with self._lock:
                    self._store.link_event(t.id, event_id, etag)
                continue

            # Deleted in the calendar -> trash the task.
            if ev is not None and ev.get("status") == "cancelled":
                with self._lock:
                    self._store.delete(t.id)
                    self._store.link_event(t.id, None)
                continue

            # Compare etags, not clocks: Google's clock and this PC's may disagree.
            remote_dirty = ev is not None and ev.get("etag") != t.gcal_etag
            # Both sides edited since the last sync: the later edit wins.
            if remote_dirty and (not local_dirty
                                 or _parse_rfc3339(ev["updated"]) > _local(datetime.fromisoformat(t.updated_at))):
                due_date, due_time = event_when(ev)
                with self._lock:
                    self._store.apply_remote(t.id, ev.get("summary", t.title), due_date, due_time, ev["etag"])
                continue

            if local_dirty:
                if t.due_date is None:  # date removed -> the event has nothing to show
                    cal.delete(t.gcal_event_id)
                    with self._lock:
                        self._store.link_event(t.id, None)
                    continue
                current = ev or cal.get(t.gcal_event_id)
                etag = current and cal.patch(t.gcal_event_id, event_body(t, event_duration(current)))
                if not etag:
                    with self._lock:  # event vanished without a trace -> treat as deleted remotely
                        self._store.delete(t.id)
                        self._store.link_event(t.id, None)
                    continue
                with self._lock:
                    self._store.mark_synced(t.id, etag)

        self.last_pull = pull_started
        self._refresh_today(cal, now)
        self.last_sync = now.strftime("%H:%M")

    def _refresh_today(self, cal, now: datetime) -> None:
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
        events = []
        for c in cal.calendars():
            if c.get("primary"):
                self.account = c["id"]
            for ev in cal.events(c["id"], start, end):
                tagged = ev.get("extendedProperties", {}).get("private", {}).get(APP_TAG) == "1"
                if ev.get("status") != "cancelled" and not tagged:  # our tasks already show as tasks
                    events.append(display_event(ev, c))
        events.sort(key=lambda e: (not e["all_day"], e["start"] or ""))
        self.today_events = events
