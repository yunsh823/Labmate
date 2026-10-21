"""Render the app's own screens with sample data into docs/images/ for the setup guide.

Uses Edge in headless mode, so nothing on the real desktop is captured and no personal
data is involved. Re-run after UI changes:

    python packaging/guide_shots.py
"""

import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "labmate" / "web"
OUT = ROOT / "docs" / "images"
EDGE = Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")
SCENES = {  # file name -> scene id understood by the mock below
    "app-01-gcal-connect.png": "gcal",
    "app-02-weather-key-place.png": "weather",
    "app-03-today.png": "today",
    "app-04-papers-settings.png": "papers-settings",
    "app-05-papers-tab.png": "papers",
    "feature-tasks.png": "tasks",
    "feature-popup.png": "popup",
}
POPUP_SCENES = {"popup"}  # rendered from popup.html at the tray panel's size

# Stands in for the Python side (window.pywebview.api) with sample data, then drives the UI to a scene.
MOCK = r"""
<style>html, body { overflow: hidden; }</style>
<script>
(() => {
  const scene = new URLSearchParams(location.search).get("scene");
  // Headless Edge won't lay out a window as narrow as the tray panel, so pin the panel to its real size.
  if (scene === "popup") document.write("<style>.popup .pop { width: 380px; height: 560px; box-sizing: border-box; }</style>");
  const iso = d => `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,"0")}-${String(d.getDate()).padStart(2,"0")}`;
  const now = new Date(); const day = n => { const d = new Date(now); d.setDate(d.getDate() + n); return iso(d); };
  let id = 0;
  const task = o => ({ id: ++id, notes: "", bucket: "today", project: "", due_date: null, due_time: null, recurrence: null,
                       done: false, completed_at: null, deleted_at: null, ...o });
  const tasks = [
    task({ title: "리뷰어 코멘트 2번 답변", project: "논문A", due_date: day(-1), bucket: "week" }),
    task({ title: "랩미팅 발표자료", due_date: day(0), due_time: "14:00", recurrence: "weekly", bucket: "week" }),
    task({ title: "Fig. 3 컬러바 수정", project: "논문A", due_date: day(3) }),
    task({ title: "ERA5 다운로드 스크립트 점검", project: "논문B" }),
    task({ title: "메일 회신", done: true, completed_at: iso(now) }),
  ];
  const hours = [["14", 21, "partly", "none", 20], ["15", 22, "partly", "none", 20], ["16", 21, "cloudy", "none", 30],
                 ["17", 20, "cloudy", "rain", 60], ["18", 18, "cloudy", "rain", 70], ["19", 17, "partly", "none", 30]]
    .map(([t, temp, sky, pty, pop]) => ({ time: t + ":00", temp, sky, pty, pop, night: +t >= 19 }));
  const papers = [
    { key: "1", title: "Persistent atmospheric blocking and compound heat extremes over East Asia", first_author: "J. Kim",
      author_count: 4, venue: "Journal of Climate", pub_date: day(-2), preprint: 0, reason_kind: "keyword",
      reason_value: "atmospheric blocking", status: "new", url: "" },
    { key: "2", title: "Sub-seasonal predictability of summer heatwaves in a warming climate", first_author: "A. Smith",
      author_count: 6, venue: "Geophysical Research Letters", pub_date: day(-3), preprint: 0, reason_kind: "seed",
      reason_value: "", status: "new", url: "" },
    { key: "3", title: "Reanalysis-based climatology of omega blocks, 1979-2025", first_author: "M. Rossi",
      author_count: 3, venue: "Journal of Geophysical Research: Atmospheres", pub_date: day(-5), preprint: 0,
      reason_kind: "journal", reason_value: "Journal of Climate", status: "saved", url: "" },
  ];
  const events = ["tasks", "popup"].includes(scene) ? [
    { title: "학회 초록 마감", all_day: true, calendar: "학회", color: "#f08c00" },
    { title: "세미나: 블로킹 예측성", start: "10:00", end: "11:00", calendar: "연구실", color: "#4f7cff" },
    { title: "지도교수 면담", start: "16:00", end: "16:30", calendar: "개인", color: "#2bb673" },
  ] : [];
  const settings = { theme: scene === "popup" ? "dark" : "light", lang: "ko", sidebar: "expanded", font: "",
                     remind: "10", papers_enabled: "on", papers_preprints: "off" };
  const ok = v => Promise.resolve(v);
  window.pywebview = { api: {
    state: () => ok({ today: iso(now), settings: { ...settings }, tasks, events, gcal_reauth: false,
      weather: { temp: 21, sky: "partly", pty: "none", night: false, tmin: 14, tmax: 22, pop_max: 70, hourly: hours, updated: "14:00" },
      counts: { today: 4, week: 0, later: 2, someday: 1, done: 1, trash: 0, papers: 2 }, projects: ["논문A", "논문B"] }),
    fonts: () => ok(["Malgun Gothic"]),
    app_info: () => ok({ hotkey: "Ctrl + Alt + T", hotkey_ok: true, autostart_supported: true, autostart: true }),
    gcal_status: () => ok({ has_client: true, connected: false, account: null, last_sync: null, error: null, needs_reauth: false }),
    weather_settings: () => ok({ has_key: true, place: "대구 동구 신천3동", grid: [89, 91], updated: "14:00", error: null }),
    search_places: () => ok({ total: 23, results: ["대구 동구", "대구 동구 신암1동", "대구 동구 신암2동", "대구 동구 신천1.2동",
                                                   "대구 동구 신천3동", "대구 동구 신천4동"].map((name, i) => ({ id: i, name })) }),
    papers_settings: () => ok({ enabled: "on", preprints: "off", notify_text: "", last_fetch: iso(now), error: "",
      notify_max: 50, seeds: [{ doi: "10.1175/JCLI-D-00-0000.1", title: "Example seed paper on blocking" }],
      keywords: ["atmospheric blocking", "heatwave"], journals: [{ id: "S1", name: "Journal of Climate" }] }),
    papers_list: () => ok({ papers, last_fetch: iso(now), error: "", has_sources: true }),
    update_status: () => ok({ current: "1.0.0", latest: null, checked: "14:00", error: null, auto: "on", can_install: true }),
  }};
  const go = view => document.querySelector(`[data-view="${view}"]`).click();
  // Scroll only the settings pane; scrollIntoView would also shift the whole page in a screenshot.
  const show = el => {
    const box = document.querySelector(".settings");
    box.scrollTop += el.getBoundingClientRect().top - box.getBoundingClientRect().top - 120;
  };
  window.addEventListener("load", () => setTimeout(async () => {
    if (scene === "gcal") { go("settings"); setTimeout(() => show(document.getElementById("gcal-actions")), 300); }
    if (scene === "weather") {
      go("settings");
      setTimeout(() => {
        show(document.getElementById("place-input"));
        const i = document.getElementById("place-input");
        i.value = "대구 동구"; i.dispatchEvent(new Event("input"));
      }, 300);
    }
    if (scene === "today") document.getElementById("weather").click();
    if (scene === "papers-settings") { go("settings"); setTimeout(() => show(document.getElementById("set-papers-enabled")), 300); }
    if (scene === "papers") go("papers");
    if (scene === "tasks") setTimeout(() => {
      openDetail(2);
      // Show the options row under the input too, half filled in.
      document.getElementById("quick-input").focus();
      document.getElementById("quick-input").value = "공동저자 미팅 자료 준비";
      document.getElementById("qa-date").value = day(2);
      document.getElementById("qa-project").value = "논문A";
    }, 300);
  }, 200));
})();
</script>
"""


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    # Edge keeps its throwaway profile open briefly after exiting; leftovers in %TEMP% are harmless.
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        site = Path(tmp) / "web"
        shutil.copytree(WEB, site)
        for page in (site / "index.html", site / "popup.html"):
            html = page.read_text(encoding="utf-8")
            page.write_text(html.replace('<script src="app.js"></script>', MOCK + '<script src="app.js"></script>'),
                            encoding="utf-8")
        for name, scene in SCENES.items():
            target = OUT / name
            target.unlink(missing_ok=True)
            popup = scene in POPUP_SCENES
            page = site / ("popup.html" if popup else "index.html")
            subprocess.run([
                str(EDGE), "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1",
                f"--user-data-dir={Path(tmp) / 'profile'}", "--window-size=1000,640",
                "--virtual-time-budget=4000",
                f"--screenshot={target}", page.as_uri() + f"?scene={scene}",
            ], check=True, capture_output=True, timeout=60)
            # msedge.exe returns at once and a background process writes the file a moment later.
            if not _wait_for(target):
                raise SystemExit(f"Edge did not write {target.name}")
            if popup:
                with Image.open(target) as shot:
                    panel = shot.crop((0, 0, 380, 560))
                panel.save(target)
            print("saved", target.relative_to(ROOT))


def _wait_for(path: Path, timeout: float = 30) -> bool:
    end, last = time.monotonic() + timeout, -1
    while time.monotonic() < end:
        size = path.stat().st_size if path.exists() else -1
        if size > 0 and size == last:  # present and no longer growing
            return True
        last = size
        time.sleep(0.5)
    return False


if __name__ == "__main__":
    main()
