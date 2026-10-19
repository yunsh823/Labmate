"""SQLite storage for tasks."""

import calendar
import os
import sqlite3
import sys
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path

BUCKETS = ("today", "week", "later", "someday")
VIEWS = BUCKETS + ("done", "trash")
RECURRENCES = ("daily", "weekly", "monthly")
TRASH_DAYS = 30

EDITABLE = {"title", "notes", "bucket", "project", "due_date", "due_time", "recurrence"}

SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
    id           INTEGER PRIMARY KEY,
    title        TEXT NOT NULL,
    notes        TEXT NOT NULL DEFAULT '',
    bucket       TEXT NOT NULL DEFAULT 'today',
    project      TEXT NOT NULL DEFAULT '',
    due_date     TEXT,             -- YYYY-MM-DD
    due_time     TEXT,             -- HH:MM
    recurrence   TEXT,             -- daily | weekly | monthly
    done         INTEGER NOT NULL DEFAULT 0,
    completed_at TEXT,
    deleted_at   TEXT,
    created_at   TEXT NOT NULL,
    updated_at   TEXT NOT NULL
);
"""


def data_dir() -> Path:
    """Per-user data folder, kept outside the install dir so updates keep data."""
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home()))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    path = base / "ToDoList"
    path.mkdir(parents=True, exist_ok=True)
    return path


def next_due(d: date, recurrence: str) -> date:
    if recurrence == "daily":
        return d + timedelta(days=1)
    if recurrence == "weekly":
        return d + timedelta(days=7)
    # monthly: same day next month, clamped to month length
    year, month = (d.year + 1, 1) if d.month == 12 else (d.year, d.month + 1)
    day = min(d.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


@dataclass
class Task:
    id: int
    title: str
    notes: str
    bucket: str
    project: str
    due_date: date | None
    due_time: str | None
    recurrence: str | None
    done: bool
    completed_at: str | None
    deleted_at: str | None

    @classmethod
    def from_row(cls, r: sqlite3.Row) -> "Task":
        return cls(
            id=r["id"], title=r["title"], notes=r["notes"], bucket=r["bucket"],
            project=r["project"],
            due_date=date.fromisoformat(r["due_date"]) if r["due_date"] else None,
            due_time=r["due_time"], recurrence=r["recurrence"], done=bool(r["done"]),
            completed_at=r["completed_at"], deleted_at=r["deleted_at"],
        )


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _to_db(key, value):
    if key == "due_date" and isinstance(value, date):
        return value.isoformat()
    return value


class Store:
    def __init__(self, path: Path | str | None = None):
        # The webview calls the API from worker threads; Api serializes access with a lock.
        self.conn = sqlite3.connect(str(path or data_dir() / "todo.db"), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)
        self.conn.execute("PRAGMA user_version = 1")
        self.conn.commit()

    # --- CRUD ---------------------------------------------------------------

    def add(self, title: str, bucket: str = "today", **fields) -> int:
        fields = {"title": title.strip(), "bucket": bucket, **fields}
        self._check(fields)
        now = _now()
        fields.update(created_at=now, updated_at=now)
        cols = ", ".join(fields)
        marks = ", ".join("?" * len(fields))
        cur = self.conn.execute(
            f"INSERT INTO tasks ({cols}) VALUES ({marks})",
            [_to_db(k, v) for k, v in fields.items()],
        )
        self.conn.commit()
        return cur.lastrowid

    def get(self, task_id: int) -> Task:
        row = self.conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if row is None:
            raise KeyError(task_id)
        return Task.from_row(row)

    def update(self, task_id: int, **fields) -> None:
        self._check(fields)
        fields["updated_at"] = _now()
        sets = ", ".join(f"{k} = ?" for k in fields)
        self.conn.execute(
            f"UPDATE tasks SET {sets} WHERE id = ?",
            [_to_db(k, v) for k, v in fields.items()] + [task_id],
        )
        self.conn.commit()

    def set_done(self, task_id: int, done: bool, today: date | None = None) -> None:
        """Mark done/undone. A recurring task is not closed; it rolls to its next due date."""
        today = today or date.today()
        task = self.get(task_id)
        if done and task.recurrence:
            due = next_due(task.due_date or today, task.recurrence)
            while due <= today:  # catch up an overdue series, keeping its weekday/day
                due = next_due(due, task.recurrence)
            # Leave the Today bucket; the due date pulls it back into Today when it arrives.
            bucket = "week" if (due - today).days <= 7 else "later"
            self.update(task_id, due_date=due, bucket=bucket)
            return
        self.conn.execute(
            "UPDATE tasks SET done = ?, completed_at = ?, updated_at = ? WHERE id = ?",
            (int(done), _now() if done else None, _now(), task_id),
        )
        self.conn.commit()

    # --- trash --------------------------------------------------------------

    def delete(self, task_id: int) -> None:
        self.conn.execute("UPDATE tasks SET deleted_at = ? WHERE id = ?", (_now(), task_id))
        self.conn.commit()

    def restore(self, task_id: int) -> None:
        self.conn.execute("UPDATE tasks SET deleted_at = NULL WHERE id = ?", (task_id,))
        self.conn.commit()

    def purge(self, task_id: int) -> None:
        self.conn.execute("DELETE FROM tasks WHERE id = ? AND deleted_at IS NOT NULL", (task_id,))
        self.conn.commit()

    def purge_old_trash(self, now: datetime | None = None) -> int:
        cutoff = ((now or datetime.now()) - timedelta(days=TRASH_DAYS)).isoformat(timespec="seconds")
        cur = self.conn.execute(
            "DELETE FROM tasks WHERE deleted_at IS NOT NULL AND deleted_at < ?", (cutoff,)
        )
        self.conn.commit()
        return cur.rowcount

    # --- queries ------------------------------------------------------------

    def list_view(self, view: str, project: str | None = None, today: date | None = None) -> list[Task]:
        """Tasks for a sidebar view.

        Today = Today bucket + anything due today or overdue + items finished today.
        Other buckets exclude what Today already shows, so a task appears in one view.
        """
        today_s = (today or date.today()).isoformat()
        alive = "deleted_at IS NULL"
        due_now = "(due_date IS NOT NULL AND due_date <= :today)"
        if view == "today":
            where = (f"{alive} AND ((done = 0 AND (bucket = 'today' OR {due_now}))"
                     " OR (done = 1 AND substr(completed_at, 1, 10) = :today))")
            order = "done, due_date IS NULL, due_date, due_time IS NULL, due_time, id"
        elif view in BUCKETS:
            where = f"{alive} AND done = 0 AND bucket = :view AND NOT {due_now}"
            order = "due_date IS NULL, due_date, due_time IS NULL, due_time, id"
        elif view == "done":
            where = f"{alive} AND done = 1"
            order = "completed_at DESC"
        elif view == "trash":
            where = "deleted_at IS NOT NULL"
            order = "deleted_at DESC"
        else:
            raise ValueError(view)
        if project:
            where += " AND project = :project"
        rows = self.conn.execute(
            f"SELECT * FROM tasks WHERE {where} ORDER BY {order}",
            {"today": today_s, "view": view, "project": project},
        ).fetchall()
        return [Task.from_row(r) for r in rows]

    def count(self, view: str, project: str | None = None, today: date | None = None) -> int:
        tasks = self.list_view(view, project, today)
        return sum(not t.done for t in tasks) if view == "today" else len(tasks)

    def projects(self) -> list[str]:
        rows = self.conn.execute(
            "SELECT DISTINCT project FROM tasks WHERE project != '' AND deleted_at IS NULL ORDER BY project"
        ).fetchall()
        return [r[0] for r in rows]

    # --- helpers ------------------------------------------------------------

    @staticmethod
    def _check(fields: dict) -> None:
        unknown = set(fields) - EDITABLE
        if unknown:
            raise ValueError(f"unknown fields: {unknown}")
        if "title" in fields and not fields["title"]:
            raise ValueError("title is empty")
        if "bucket" in fields and fields["bucket"] not in BUCKETS:
            raise ValueError(f"bad bucket: {fields['bucket']}")
        if fields.get("recurrence") not in (None, *RECURRENCES):
            raise ValueError(f"bad recurrence: {fields['recurrence']}")
