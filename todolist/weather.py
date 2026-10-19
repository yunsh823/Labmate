"""KMA (기상청) API Hub short-range forecast for the header weather widget.

Two calls per refresh: ultra-short-range observations (current temperature and
precipitation) and the short-range forecast (sky, hourly temperature,
precipitation probability). Today's min/max come from the 02:00 forecast run,
the one that carries them for the whole day.
"""

import json
import math
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta

BASE_URL = "https://apihub.kma.go.kr/api/typ02/openApi/VilageFcstInfoService_2.0"
FCST_HOURS = (2, 5, 8, 11, 14, 17, 20, 23)  # short-range forecast runs
SKY = {"1": "clear", "3": "partly", "4": "cloudy"}
PTY = {"0": "none", "1": "rain", "2": "sleet", "3": "snow", "4": "shower",
       "5": "rain", "6": "sleet", "7": "snow"}  # 5-7 only appear in observations (drizzle etc.)


class WeatherError(Exception):
    pass


def latlon_to_grid(lat: float, lon: float) -> tuple[int, int]:
    """KMA DFS grid (Lambert conformal conic, 5 km) from WGS84 lat/lon."""
    re, grid, slat1, slat2, olon, olat, xo, yo = 6371.00877, 5.0, 30.0, 60.0, 126.0, 38.0, 43, 136
    rad = math.pi / 180.0
    re /= grid
    slat1, slat2, olon, olat = slat1 * rad, slat2 * rad, olon * rad, olat * rad
    sn = math.log(math.cos(slat1) / math.cos(slat2)) / math.log(
        math.tan(math.pi * 0.25 + slat2 * 0.5) / math.tan(math.pi * 0.25 + slat1 * 0.5))
    sf = math.tan(math.pi * 0.25 + slat1 * 0.5) ** sn * math.cos(slat1) / sn
    ro = re * sf / math.tan(math.pi * 0.25 + olat * 0.5) ** sn
    ra = re * sf / math.tan(math.pi * 0.25 + lat * rad * 0.5) ** sn
    theta = lon * rad - olon
    theta = (theta + math.pi) % (2 * math.pi) - math.pi
    theta *= sn
    return int(ra * math.sin(theta) + xo + 0.5), int(ro - ra * math.cos(theta) + yo + 0.5)


# --- which forecast run to ask for ------------------------------------------------

def ncst_base(now: datetime) -> tuple[str, str]:
    """Observations for HH:00 are published around HH:40."""
    t = now - timedelta(minutes=40)
    return t.strftime("%Y%m%d"), t.strftime("%H00")


def fcst_base(now: datetime) -> tuple[str, str]:
    """Latest short-range run; each is available about 10 minutes after its hour."""
    t = now - timedelta(minutes=10)
    runs = [h for h in FCST_HOURS if h <= t.hour]
    if not runs:  # before 02:10 -> yesterday's 23:00 run
        t -= timedelta(days=1)
        return t.strftime("%Y%m%d"), "2300"
    return t.strftime("%Y%m%d"), f"{runs[-1]:02d}00"


def daily_base(now: datetime) -> tuple[str, str]:
    """The run that holds today's TMN/TMX: today 02:00, or yesterday 23:00 before it's out."""
    if now - timedelta(minutes=10) >= now.replace(hour=2, minute=0, second=0, microsecond=0):
        return now.strftime("%Y%m%d"), "0200"
    return (now - timedelta(days=1)).strftime("%Y%m%d"), "2300"


# --- HTTP -------------------------------------------------------------------------

def fetch(op: str, key: str, base: tuple[str, str], grid: tuple[int, int]) -> list[dict]:
    query = urllib.parse.urlencode({
        "pageNo": 1, "numOfRows": 1000, "dataType": "JSON",
        "base_date": base[0], "base_time": base[1], "nx": grid[0], "ny": grid[1], "authKey": key,
    })
    try:
        with urllib.request.urlopen(f"{BASE_URL}/{op}?{query}", timeout=15) as resp:
            body = resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        # API Hub explains auth problems in a JSON body; never echo the URL (it holds the key).
        try:
            msg = json.loads(e.read().decode("utf-8", "replace"))["result"]["message"]
        except Exception:
            msg = f"HTTP {e.code}"
        raise WeatherError(msg) from None
    except urllib.error.URLError as e:
        raise WeatherError(str(e.reason)) from None
    try:
        data = json.loads(body)["response"]
    except (ValueError, KeyError):
        raise WeatherError(body[:120]) from None
    if data["header"]["resultCode"] != "00":
        raise WeatherError(data["header"]["resultMsg"])
    return data["body"]["items"]["item"]


# --- summary for the UI ---------------------------------------------------------

def summarize(ncst: list[dict], fcst: list[dict], daily: list[dict], now: datetime) -> dict:
    obs = {i["category"]: i["obsrValue"] for i in ncst}
    today = now.strftime("%Y%m%d")

    hours: dict[str, dict] = {}  # "YYYYMMDDHHMM" -> {category: value}
    for i in fcst:
        hours.setdefault(i["fcstDate"] + i["fcstTime"], {})[i["category"]] = i["fcstValue"]
    upcoming = sorted(k for k in hours if k >= now.strftime("%Y%m%d%H00"))

    hourly = []
    for k in upcoming:
        if k[:8] != today and len(hourly) >= 6:  # rest of today, at least 6 hours ahead
            break
        h = hours[k]
        if "TMP" not in h:
            continue
        hourly.append({
            "time": f"{k[8:10]}:00", "temp": round(float(h["TMP"])),
            "sky": SKY.get(h.get("SKY"), "clear"), "pty": PTY.get(h.get("PTY", "0"), "none"),
            "pop": int(h.get("POP", 0)), "night": not 6 <= int(k[8:10]) < 19,
        })

    def daily_value(cat):
        vals = [float(i["fcstValue"]) for i in daily if i["category"] == cat and i["fcstDate"] == today]
        return round(vals[0]) if vals else None

    first = hours[upcoming[0]] if upcoming else {}
    pops_today = [int(hours[k].get("POP", 0)) for k in upcoming if k[:8] == today]
    current_pty = PTY.get(obs.get("PTY", "0"), "none")
    return {
        "temp": round(float(obs["T1H"])) if "T1H" in obs else (hourly[0]["temp"] if hourly else None),
        "sky": SKY.get(first.get("SKY"), "clear"),
        "pty": current_pty if current_pty != "none" else PTY.get(first.get("PTY", "0"), "none"),
        "night": not 6 <= now.hour < 19,
        "tmin": daily_value("TMN"), "tmax": daily_value("TMX"),
        "pop_max": max(pops_today, default=0),
        "hourly": hourly,
        "updated": now.strftime("%H:%M"),
    }


class Weather:
    def __init__(self):
        self.data: dict | None = None
        self.error: str | None = None
        self._daily: tuple[tuple[str, str], tuple[int, int], list[dict]] | None = None  # cache per run+grid

    def refresh(self, key: str, lat: float, lon: float, now: datetime | None = None) -> None:
        now = now or datetime.now()
        grid = latlon_to_grid(lat, lon)
        try:
            ncst = fetch("getUltraSrtNcst", key, ncst_base(now), grid)
            fcst = fetch("getVilageFcst", key, fcst_base(now), grid)
            dbase = daily_base(now)
            if self._daily is None or self._daily[:2] != (dbase, grid):
                self._daily = (dbase, grid, fetch("getVilageFcst", key, dbase, grid))
            self.data = summarize(ncst, fcst, self._daily[2], now)
            self.error = None
        except WeatherError as e:
            self.error = str(e)
