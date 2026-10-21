import json
from datetime import date

import pytest

from labmate.api import Api
from labmate.db import Store


@pytest.fixture
def api(tmp_path):
    return Api(Store(tmp_path / "test.db"))


def test_state_is_json_serializable(api):
    api.add("Fix Fig. 3", project="Paper A")
    state = api.state("today")
    json.dumps(state)  # must not raise
    assert state["today"] == date.today().isoformat()
    assert [t["title"] for t in state["tasks"]] == ["Fix Fig. 3"]
    assert state["counts"]["today"] == 1
    assert state["projects"] == ["Paper A"]


def test_add_falls_back_to_today_for_non_bucket_views(api):
    tid = api.add("x", bucket="trash")
    assert api._store.get(tid).bucket == "today"


def test_update_maps_empty_form_values(api):
    tid = api.add("x", project="Paper A")
    api.update(tid, {"due_date": "2026-10-22", "due_time": "14:00", "recurrence": "weekly"})
    t = api._store.get(tid)
    assert (t.due_date, t.due_time, t.recurrence) == (date(2026, 10, 22), "14:00", "weekly")

    api.update(tid, {"due_date": "", "recurrence": "", "project": ""})
    t = api._store.get(tid)
    assert t.due_date is None and t.due_time is None  # time cleared with the date
    assert t.recurrence is None
    assert t.project == ""


def test_project_filter_passthrough(api):
    api.add("a", project="Paper A")
    api.add("b")
    assert [t["title"] for t in api.state("today", "Paper A")["tasks"]] == ["a"]
    assert len(api.state("today", "")["tasks"]) == 2


def test_settings_persist_and_validate(api, tmp_path):
    assert api.state("today")["settings"] == {"theme": "system", "lang": "ko", "sidebar": "expanded", "font": "",
                                              "remind": "10", "papers_enabled": "on", "papers_preprints": "off",
                                              "update_auto": "on"}
    api.set_setting("theme", "dark")
    api.set_setting("lang", "en")
    api.set_setting("font", "Malgun Gothic")
    reopened = Api(Store(tmp_path / "test.db")).state("today")["settings"]
    assert reopened["theme"] == "dark" and reopened["lang"] == "en" and reopened["font"] == "Malgun Gothic"
    for key, bad in [("theme", "blue"), ("lang", "jp"), ("font", 'x"; color:red')]:
        with pytest.raises(ValueError):
            api.set_setting(key, bad)
    with pytest.raises(KeyError):
        api.set_setting("unknown", "x")


def test_fonts_lists_system_families(api):
    fonts = api.fonts()
    assert fonts and not any(f.startswith("@") for f in fonts)


def test_weather_place_and_key(api, monkeypatch):
    calls = []
    monkeypatch.setattr(api._weather, "refresh", lambda key, grid: calls.append(grid))  # no network
    st = api.set_weather_key("abc123")
    assert st["has_key"] and "abc123" not in str(st) and calls == []  # no place yet -> no fetch
    found = api.search_places("대구 동구 신천3")
    assert found["total"] == 1
    st = api.set_weather_place(found["results"][0]["id"])
    assert st["place"] == "대구 동구 신천3동" and st["grid"] == (89, 91) and calls == [(89, 91)]
    assert "abc123" not in str(api.state("today"))
    for bad in ["", "a b"]:
        with pytest.raises(ValueError):
            api.set_weather_key(bad)


def test_weather_location_from_earlier_version_still_works(api):
    api._store.set_setting("weather_lat", "37.5665")
    api._store.set_setting("weather_lon", "126.9780")
    assert api.weather_settings()["grid"] == (60, 127)


def test_paper_alert_settings(api, monkeypatch):
    from labmate import papers
    monkeypatch.setattr(papers, "lookup_title", lambda doi: "Blocking and heatwaves")
    st = api.add_paper_seed("https://doi.org/10.1175/JCLI-D-17-0034.1")
    assert st["seeds"] == [{"doi": "10.1175/JCLI-D-17-0034.1", "title": "Blocking and heatwaves"}]
    api.add_paper_seed("10.1175/jcli-d-17-0034.1")  # same DOI, different case: not added twice
    assert len(api.papers_settings()["seeds"]) == 1
    with pytest.raises(ValueError, match="bad_doi"):
        api.add_paper_seed("not a doi")
    api.add_paper_keyword("atmospheric, blocking")
    assert api.papers_settings()["keywords"] == ["atmospheric blocking"]
    for i in range(9):
        api.add_paper_keyword(f"k{i}")
    with pytest.raises(ValueError, match="too_many"):
        api.add_paper_keyword("one too many")
    assert api.papers_settings()["preprints"] == "off"  # most people never read preprints


def test_paper_notify_text_limit(api):
    assert api.set_papers_notify_text("  오늘의   논문 도착!  ")["notify_text"] == "오늘의 논문 도착!"
    assert api.set_papers_notify_text("")["notify_text"] == ""  # empty -> default line
    with pytest.raises(ValueError, match="too_long"):
        api.set_papers_notify_text("가" * 51)


def test_fetch_and_save_paper(api, monkeypatch):
    from labmate import papers
    paper = {"key": "10.1/p", "doi": "10.1/p", "title": "A paper", "first_author": "Kim", "author_count": 3,
             "venue": "GRL", "pub_date": "2026-10-18", "url": "https://doi.org/10.1/p", "preprint": 0,
             "reason_kind": "keyword", "reason_value": "blocking"}
    monkeypatch.setattr(papers, "fetch", lambda *a, **k: ([paper], None))
    assert api._papers_due() is False  # nothing configured yet
    api.add_paper_keyword("blocking")
    assert api._papers_due() is True
    assert api._fetch_papers() == (1, None)
    assert api._papers_due() is False  # done for today
    assert api.state("today")["counts"]["papers"] == 1
    listed = api.papers_list()
    assert [p["title"] for p in listed["papers"]] == ["A paper"]
    assert api.state("today")["counts"]["papers"] == 0  # opening the tab marks them seen
    api.save_paper("10.1/p")
    later = api.state("later")["tasks"]
    assert later[0]["title"] == "읽기: A paper" and later[0]["notes"] == "https://doi.org/10.1/p"


def test_total_fetch_failure_is_retried_not_skipped(api, monkeypatch):
    from labmate import papers
    monkeypatch.setattr(papers, "fetch", lambda *a, **k: ([], "network"))
    api.add_paper_keyword("blocking")
    assert api._fetch_papers() == (0, "network")
    assert api._papers_due() is True and api.papers_settings()["error"] == "network"


def test_internal_attributes_hidden_from_js(api):
    public = [n for n in vars(api) if not n.startswith("_")]
    assert public == []


def test_calendar_colors_apply_to_events(api):
    api._gcal.calendars = [{"id": "c1", "name": "Lab", "color": "#4f6bed"}]
    api._gcal.today_events = [{"title": "Seminar", "calendar_id": "c1", "color": "#4f6bed"}]
    st = api.set_calendar_color("c1", "#33b679")
    assert st["calendars"][0]["custom"] == "#33b679"
    assert api.state("today")["events"][0]["color"] == "#33b679"
    api.set_calendar_color("c1", "")
    assert api.state("today")["events"][0]["color"] == "#4f6bed"
    with pytest.raises(ValueError):
        api.set_calendar_color("c1", "red; background:url(x)")


def test_update_check(api, monkeypatch):
    from labmate import updater
    assert api._update_due()
    monkeypatch.setattr(updater, "latest", lambda: {"version": "9.9.9"})
    st = api.check_update_now()
    assert st["latest"] == "9.9.9" and st["error"] is None and not api._update_due()
    with pytest.raises(ValueError, match="dev"):
        api.install_update()  # tests run from source, never frozen
    api.set_setting("update_auto", "off")
    api._update_checked = None
    assert not api._update_due()
