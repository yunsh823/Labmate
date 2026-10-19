"""Which timed tasks and calendar events should be announced now."""

from datetime import datetime, time, timedelta

from .db import Task


def due_reminders(now: datetime, tasks: list[Task], events: list[dict],
                  lead: timedelta, sent: set[str]) -> list[tuple[str, str, datetime]]:
    """(key, title, start) for today's items starting within `lead`, not yet announced.

    `now` is naive local time. Keys identify an item at a given time, so a task
    moved to a new time is announced again.
    """
    today = now.date()
    items = [(f"task:{t.id}:{t.due_date}:{t.due_time}", t.title, t.due_time)
             for t in tasks if t.due_date == today and t.due_time and not t.done and not t.deleted_at]
    items += [(f"event:{e['title']}:{e['start']}", e["title"], e["start"])
              for e in events if not e["all_day"]]
    out = []
    for key, title, hhmm in items:
        start = datetime.combine(today, time.fromisoformat(hhmm))
        if key not in sent and timedelta(0) <= start - now <= lead:
            out.append((key, title, start))
    return sorted(out, key=lambda x: x[2])
