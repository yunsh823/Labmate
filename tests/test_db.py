from datetime import date, datetime, timedelta

import pytest

from labmate import db
from labmate.db import Store, bucket_for_due, next_due

TODAY = date(2026, 10, 19)  # Monday


@pytest.fixture
def store(tmp_path):
    return Store(tmp_path / "test.db")


def ids(tasks):
    return [t.id for t in tasks]


def test_add_and_get(store):
    tid = store.add("  Fix Fig. 3  ", project="Paper A", due_date=date(2026, 10, 25))
    t = store.get(tid)
    assert t.title == "Fix Fig. 3"
    assert t.bucket == bucket_for_due(date(2026, 10, 25), date.today())  # a dated task is filed by its date
    assert t.project == "Paper A"
    assert t.due_date == date(2026, 10, 25)


def test_rejects_bad_input(store):
    with pytest.raises(ValueError):
        store.add("   ")
    with pytest.raises(ValueError):
        store.add("x", bucket="tomorrow")
    with pytest.raises(ValueError):
        store.add("x", recurrence="yearly")


def test_today_pulls_in_due_and_overdue(store):
    in_today = store.add("today bucket")
    overdue = store.add("overdue", bucket="later", due_date=TODAY - timedelta(days=2))
    due_today = store.add("due today", bucket="someday", due_date=TODAY)
    future = store.add("future", bucket="week", due_date=TODAY + timedelta(days=3))

    assert set(ids(store.list_view("today", today=TODAY))) == {in_today, overdue, due_today}
    # each task shows in exactly one view
    assert ids(store.list_view("week", today=TODAY)) == [future]
    assert ids(store.list_view("later", today=TODAY)) == []
    assert ids(store.list_view("someday", today=TODAY)) == []


def test_done_today_stays_visible_but_not_counted(store):
    tid = store.add("write abstract")
    store.set_done(tid, True)
    today = date.today()
    assert ids(store.list_view("today", today=today)) == [tid]
    assert store.count("today", today=today) == 0
    assert ids(store.list_view("done")) == [tid]
    store.set_done(tid, False)
    assert store.count("today", today=today) == 1


def test_recurring_rolls_forward_instead_of_closing(store):
    tid = store.add("lab meeting prep", recurrence="weekly", due_date=TODAY)
    store.set_done(tid, True, today=TODAY)
    t = store.get(tid)
    assert not t.done
    assert t.due_date == TODAY + timedelta(days=7)
    assert t.bucket == "later"  # 7 days out is just past This week; it moves in the next day
    assert tid not in ids(store.list_view("today", today=TODAY))
    assert tid in ids(store.list_view("today", today=TODAY + timedelta(days=7)))


def test_overdue_recurring_catches_up_keeping_weekday(store):
    tid = store.add("weekly report", recurrence="weekly", due_date=TODAY - timedelta(days=15))
    store.set_done(tid, True, today=TODAY)
    due = store.get(tid).due_date
    assert due > TODAY
    assert due.weekday() == (TODAY - timedelta(days=15)).weekday()


def test_next_due_monthly_clamps():
    assert next_due(date(2026, 1, 31), "monthly") == date(2026, 2, 28)
    assert next_due(date(2026, 12, 15), "monthly") == date(2027, 1, 15)
    assert next_due(date(2026, 10, 19), "daily") == date(2026, 10, 20)


def test_trash_restore_and_purge(store):
    tid = store.add("draft email")
    store.delete(tid)
    assert ids(store.list_view("today", today=TODAY)) == []
    assert ids(store.list_view("trash")) == [tid]
    store.restore(tid)
    assert ids(store.list_view("today", today=TODAY)) == [tid]
    store.delete(tid)
    store.purge(tid)
    with pytest.raises(KeyError):
        store.get(tid)


def test_purge_only_alive_tasks_is_noop(store):
    tid = store.add("keep me")
    store.purge(tid)  # not in trash -> must not delete
    assert store.get(tid).title == "keep me"


def test_old_trash_auto_purged(store):
    old = store.add("old")
    recent = store.add("recent")
    store.delete(old)
    store.delete(recent)
    store.conn.execute("UPDATE tasks SET deleted_at = '2000-01-01T00:00:00' WHERE id = ?", (old,))
    assert store.purge_old_trash(datetime.now()) == 1
    assert ids(store.list_view("trash")) == [recent]


def test_project_filter_and_list(store):
    a = store.add("a", project="Paper A")
    store.add("b", project="Paper B")
    store.add("c")
    assert ids(store.list_view("today", project="Paper A", today=TODAY)) == [a]
    assert store.projects() == ["Paper A", "Paper B"]


def test_data_dir_moves_old_folder(tmp_path, monkeypatch):
    monkeypatch.setattr(db.sys, "platform", "win32")
    monkeypatch.setenv("APPDATA", str(tmp_path))
    (tmp_path / "ToDoList").mkdir()
    (tmp_path / "ToDoList" / "todo.db").write_text("x")
    assert db.data_dir() == tmp_path / "Labmate"
    assert (tmp_path / "Labmate" / "todo.db").read_text() == "x"
    assert not (tmp_path / "ToDoList").exists()


def test_bucket_for_due():
    assert [bucket_for_due(TODAY + timedelta(days=n), TODAY) for n in (-2, 0, 1, 6, 7, 30)] ==         ["today", "today", "week", "week", "later", "later"]


def test_dated_tasks_follow_their_date(store):
    a = store.add("Due today", bucket="later", due_date=TODAY)
    b = store.add("In 3 days", bucket="today", due_date=TODAY + timedelta(days=3))
    c = store.add("In 6 days", due_date=TODAY + timedelta(days=6))
    d = store.add("In 7 days", bucket="week", due_date=TODAY + timedelta(days=7))
    e = store.add("Undated idea", bucket="someday")
    assert ids(store.list_view("today", today=TODAY)) == [a]
    assert ids(store.list_view("week", today=TODAY)) == [b, c]
    assert ids(store.list_view("later", today=TODAY)) == [d]
    assert ids(store.list_view("someday", today=TODAY)) == [e]
    # As the days pass, the Later task comes into This week and then into Today.
    assert d in ids(store.list_view("week", today=TODAY + timedelta(days=1)))
    assert d in ids(store.list_view("today", today=TODAY + timedelta(days=7)))


def test_project_view_shows_the_whole_project(store):
    a = store.add("Today", project="P")
    b = store.add("Later", project="P", due_date=TODAY + timedelta(days=30))
    c = store.add("Idea", project="P", bucket="someday")
    d = store.add("Done", project="P")
    store.set_done(d, True)
    store.add("Other project", project="Q")
    assert sorted(ids(store.list_view("project", "P", TODAY))) == sorted([a, b, c, d])
    with pytest.raises(ValueError):
        store.list_view("project", None, TODAY)
