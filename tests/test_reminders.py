from datetime import date, datetime, timedelta

from todolist.db import Task
from todolist.reminders import due_reminders

NOW = datetime(2026, 10, 19, 13, 52)
LEAD = timedelta(minutes=10)


def task(id, due_time, due_date=date(2026, 10, 19), done=False, deleted_at=None):
    return Task(id=id, title=f"t{id}", notes="", bucket="today", project="", due_date=due_date,
                due_time=due_time, recurrence=None, done=done, completed_at=None, deleted_at=deleted_at)


def event(title, start, all_day=False):
    return {"title": title, "start": start, "end": None, "all_day": all_day, "calendar": "", "color": ""}


def test_picks_items_inside_lead_window_only():
    tasks = [task(1, "14:00"), task(2, "14:30"), task(3, "13:40"),           # in / too far / already started
             task(4, "14:00", done=True), task(5, "14:00", deleted_at="x"),  # done / trashed
             task(6, "14:00", due_date=date(2026, 10, 20))]                  # another day
    events = [event("Seminar", "13:55"), event("Holiday", None, all_day=True)]
    got = due_reminders(NOW, tasks, events, LEAD, set())
    assert [title for _, title, _ in got] == ["Seminar", "t1"]


def test_does_not_repeat_but_reannounces_when_time_changes():
    sent = set()
    first = due_reminders(NOW, [task(1, "14:00")], [], LEAD, sent)
    sent.update(k for k, _, _ in first)
    assert due_reminders(NOW, [task(1, "14:00")], [], LEAD, sent) == []
    assert len(due_reminders(NOW, [task(1, "13:58")], [], LEAD, sent)) == 1
