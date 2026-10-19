"""Bridge exposed to the web UI as window.pywebview.api.

Every method returns JSON-serializable data. Names starting with "_" are
hidden from JavaScript.
"""

import threading
from dataclasses import asdict
from datetime import date

from .db import BUCKETS, VIEWS, Store, Task


def _task_dict(t: Task) -> dict:
    d = asdict(t)
    d["due_date"] = t.due_date.isoformat() if t.due_date else None
    return d


class Api:
    def __init__(self, store: Store):
        self._store = store
        self._lock = threading.Lock()

    def state(self, view: str, project: str | None = None) -> dict:
        """Everything one render needs, in a single round trip."""
        with self._lock:
            today = date.today()
            project = project or None
            return {
                "today": today.isoformat(),
                "tasks": [_task_dict(t) for t in self._store.list_view(view, project, today)],
                "counts": {v: self._store.count(v, project, today) for v in VIEWS},
                "projects": self._store.projects(),
            }

    def add(self, title: str, bucket: str = "today", project: str = "") -> int:
        with self._lock:
            return self._store.add(title, bucket=bucket if bucket in BUCKETS else "today",
                                   project=project or "")

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

    def set_done(self, task_id: int, done: bool) -> None:
        with self._lock:
            self._store.set_done(task_id, done)

    def delete(self, task_id: int) -> None:
        with self._lock:
            self._store.delete(task_id)

    def restore(self, task_id: int) -> None:
        with self._lock:
            self._store.restore(task_id)

    def purge(self, task_id: int) -> None:
        with self._lock:
            self._store.purge(task_id)
