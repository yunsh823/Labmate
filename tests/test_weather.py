from datetime import datetime

from labmate.weather import daily_base, fcst_base, latlon_to_grid, ncst_base, summarize


def test_grid_matches_kma_reference_points():
    assert latlon_to_grid(37.5665, 126.9780) == (60, 127)  # Seoul City Hall
    assert latlon_to_grid(33.4996, 126.5312) == (53, 38)   # Jeju City


def test_base_times():
    assert ncst_base(datetime(2026, 10, 19, 14, 39)) == ("20261019", "1300")
    assert ncst_base(datetime(2026, 10, 19, 14, 41)) == ("20261019", "1400")
    assert ncst_base(datetime(2026, 10, 19, 0, 10)) == ("20261018", "2300")
    assert fcst_base(datetime(2026, 10, 19, 14, 5)) == ("20261019", "1100")
    assert fcst_base(datetime(2026, 10, 19, 14, 15)) == ("20261019", "1400")
    assert fcst_base(datetime(2026, 10, 19, 1, 0)) == ("20261018", "2300")
    assert daily_base(datetime(2026, 10, 19, 15, 0)) == ("20261019", "0200")
    assert daily_base(datetime(2026, 10, 19, 2, 5)) == ("20261018", "2300")


def fc(date, time, cat, value):
    return {"baseDate": "20261019", "baseTime": "1400", "category": cat, "fcstDate": date,
            "fcstTime": time, "fcstValue": value, "nx": 60, "ny": 127}


def test_summarize_builds_widget_data():
    now = datetime(2026, 10, 19, 21, 20)
    ncst = [{"category": "T1H", "obsrValue": "17.6"}, {"category": "PTY", "obsrValue": "0"}]
    fcst = []
    for hh, tmp, sky, pty, pop in [("2100", "17", "1", "0", "10"), ("2200", "16", "3", "0", "20"),
                                   ("2300", "15", "4", "1", "70")]:
        fcst += [fc("20261019", hh, "TMP", tmp), fc("20261019", hh, "SKY", sky),
                 fc("20261019", hh, "PTY", pty), fc("20261019", hh, "POP", pop)]
    for hh in ("0000", "0100", "0200", "0300", "0400", "0500"):
        fcst += [fc("20261020", hh, "TMP", "14"), fc("20261020", hh, "SKY", "1"), fc("20261020", hh, "POP", "0")]
    daily = [fc("20261019", "0600", "TMN", "9.0"), fc("20261019", "1500", "TMX", "21.0"),
             fc("20261020", "0600", "TMN", "8.0")]

    w = summarize(ncst, fcst, daily, now)
    assert (w["temp"], w["tmin"], w["tmax"]) == (18, 9, 21)
    assert w["sky"] == "clear" and w["pty"] == "none" and w["night"] is True
    assert w["pop_max"] == 70  # umbrella hint comes from the rest of today
    assert [h["time"] for h in w["hourly"]][:3] == ["21:00", "22:00", "23:00"]
    assert len(w["hourly"]) == 6  # at least six hours even past midnight
    assert w["hourly"][2]["pty"] == "rain"


def test_current_precipitation_comes_from_observation():
    now = datetime(2026, 10, 19, 15, 0)
    ncst = [{"category": "T1H", "obsrValue": "12"}, {"category": "PTY", "obsrValue": "3"}]
    fcst = [fc("20261019", "1500", "TMP", "12"), fc("20261019", "1500", "SKY", "4"), fc("20261019", "1500", "PTY", "0")]
    assert summarize(ncst, fcst, [], now)["pty"] == "snow"
