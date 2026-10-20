import json
from datetime import date

import pytest

from todolist.api import Api
from todolist.db import Store


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
                                              "remind": "10"}
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


def test_internal_attributes_hidden_from_js(api):
    public = [n for n in vars(api) if not n.startswith("_")]
    assert public == []
