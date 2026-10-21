"""Desktop shell: main window, tray icon, and the Today popup above the taskbar."""

import ctypes
import sys
import threading
import time
from ctypes import wintypes
from datetime import datetime, timedelta
from pathlib import Path

import pystray
import webview
from PIL import Image, ImageDraw, ImageFont

from .api import Api
from .db import Store, data_dir
from .reminders import due_reminders

WEB_DIR = Path(__file__).parent / "web"
POPUP_W, POPUP_H, MARGIN = 380, 560, 12
ACCENT = (79, 107, 237)

TRAY_TEXT = {
    "ko": {"today": "오늘 할 일", "main": "전체 창 열기", "quit": "종료",
           "open": "Labmate · 오늘 남은 할 일 {n}개", "clear": "Labmate · 오늘 할 일을 모두 끝냈어요",
           "soon": "{m}분 후 시작", "soon_many": "곧 시작하는 일정 {n}개",
           "papers": "새 논문이 도착했어요.", "papers_title": "Labmate · 새 논문 {n}편",
           "update": "업데이트 설치 (v{v})", "update_title": "Labmate · 새 버전 {v}",
           "update_body": "트레이 메뉴나 설정에서 업데이트할 수 있어요.",
           "update_failed": "업데이트를 받지 못했어요. 잠시 후 다시 시도해 주세요."},
    "en": {"today": "Today", "main": "Open full window", "quit": "Quit",
           "open": "Labmate · {n} left today", "clear": "Labmate · All done for today",
           "soon": "Starts in {m} min", "soon_many": "{n} items starting soon",
           "papers": "New papers have arrived.", "papers_title": "Labmate · {n} new papers",
           "update": "Install update (v{v})", "update_title": "Labmate · Version {v} is out",
           "update_body": "Update from the tray menu or Settings.",
           "update_failed": "Couldn't download the update. Please try again later."},
}


def _font(size: int) -> ImageFont.FreeTypeFont:
    for name in ("segoeuib.ttf", "arialbd.ttf", "Arial Bold.ttf", "DejaVuSans-Bold.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default(size)


def make_icon(count: int = 0, size: int = 64) -> Image.Image:
    """Accent tile showing today's open count, or a check mark when nothing is left."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((2, 2, size - 3, size - 3), radius=size // 4, fill=ACCENT)
    if count:
        text = str(count) if count < 10 else "9+"
        d.text((size / 2, size / 2), text, font=_font(int(size * (0.62 if count < 10 else 0.46))),
               fill="white", anchor="mm")
    else:
        s = size / 64
        d.line([(18 * s, 33 * s), (28 * s, 43 * s), (46 * s, 23 * s)], fill="white",
               width=round(7 * s), joint="curve")
    return img


def _popup_position() -> tuple[int, int]:
    """Bottom-right corner of the desktop area not covered by the taskbar, in logical px."""
    if sys.platform == "win32":
        class RECT(ctypes.Structure):
            _fields_ = [(n, ctypes.c_long) for n in ("left", "top", "right", "bottom")]
        r = RECT()
        ctypes.windll.user32.SystemParametersInfoW(0x30, 0, ctypes.byref(r), 0)  # SPI_GETWORKAREA
        scale = ctypes.windll.user32.GetDpiForSystem() / 96
        return int(r.right / scale - POPUP_W - MARGIN), int(r.bottom / scale - POPUP_H - MARGIN)
    # macOS/Linux: top-right, under the menu bar
    screen = webview.screens[0]
    return screen.width - POPUP_W - MARGIN, 40


def _hide_from_taskbar(window: webview.Window) -> None:
    """Make the popup a tool window so it doesn't get its own taskbar button."""
    if sys.platform != "win32" or window.native is None:
        return
    GWL_EXSTYLE, WS_EX_TOOLWINDOW, WS_EX_APPWINDOW = -20, 0x80, 0x40000
    user32 = ctypes.windll.user32
    hwnd = window.native.Handle.ToInt64()
    style = user32.GetWindowLongPtrW(ctypes.c_void_p(hwnd), GWL_EXSTYLE)
    user32.SetWindowLongPtrW(ctypes.c_void_p(hwnd), GWL_EXSTYLE,
                             (style | WS_EX_TOOLWINDOW) & ~WS_EX_APPWINDOW)


class Desktop:
    HOTKEY_LABEL = "Ctrl + Alt + T"

    def __init__(self, store: Store):
        self.api = Api(store, shell=self)
        self.quitting = False
        self.popup_visible = False
        self.popup_hidden_at = 0.0
        self.popup_shown_at = 0.0
        self._sync_wakeup = threading.Event()
        self.hotkey_ok = False
        self._reminded: set[str] = set()
        self._papers_retry_at = 0.0
        self._update_notified: str | None = None

        self.main = webview.create_window(
            "Labmate", url=str(WEB_DIR / "index.html"), js_api=self.api,
            width=1080, height=720, min_size=(760, 480),
        )
        self.popup = webview.create_window(
            "Labmate Today", url=str(WEB_DIR / "popup.html"), js_api=self.api,
            width=POPUP_W, height=POPUP_H, frameless=True, easy_drag=False,
            resizable=False, on_top=True, hidden=True,
        )
        self.main.events.closing += self._on_main_closing

        self.icon = pystray.Icon("Labmate", make_icon(), "Labmate", menu=pystray.Menu(
            # default=True: a left click on the tray icon runs this item.
            # Labels are callables so they follow the language setting.
            pystray.MenuItem(lambda item: self._text("today"), lambda icon, item: self.toggle_popup(), default=True),
            pystray.MenuItem(lambda item: self._text("main"), lambda icon, item: self.show_main()),
            pystray.MenuItem(lambda item: self._text("update").format(v=(self.api._update_info or {}).get("version")),
                             lambda icon, item: self._install_update(), visible=lambda item: bool(self.api._update_info)),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(lambda item: self._text("quit"), lambda icon, item: self.quit()),
        ))

    def run(self, debug: bool = False) -> None:
        icon_path = data_dir() / "app.ico"
        make_icon(size=256).save(icon_path, sizes=[(16, 16), (32, 32), (48, 48), (256, 256)])
        threading.Thread(target=self.icon.run, daemon=True).start()
        webview.start(self._on_started, debug=debug, icon=str(icon_path))

    def _on_started(self) -> None:
        _hide_from_taskbar(self.popup)
        threading.Thread(target=self._sync_loop, daemon=True).start()
        threading.Thread(target=self._weather_loop, daemon=True).start()
        if sys.platform == "win32":
            threading.Thread(target=self._hotkey_loop, daemon=True).start()
        # Tray count (also across midnight) and reminders.
        while not self.quitting:
            self.refresh_icon()
            self._check_reminders()
            self._check_papers()
            self._check_update()
            time.sleep(30)

    def _hotkey_loop(self) -> None:
        """Global Ctrl+Alt+T opens the popup ready to type a task."""
        MOD_ALT, MOD_CONTROL, MOD_NOREPEAT, WM_HOTKEY = 0x1, 0x2, 0x4000, 0x0312
        user32 = ctypes.windll.user32
        # Registered to this thread (no window), so WM_HOTKEY arrives in its message queue.
        self.hotkey_ok = bool(user32.RegisterHotKey(None, 1, MOD_CONTROL | MOD_ALT | MOD_NOREPEAT, ord("T")))
        if not self.hotkey_ok:
            return  # taken by another program; Settings shows it as unavailable
        msg = wintypes.MSG()
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
            if msg.message == WM_HOTKEY:
                self.quick_add()

    def _check_papers(self) -> None:
        """Once a day; a failed attempt (offline at boot, say) is retried after 30 minutes."""
        if time.monotonic() < self._papers_retry_at or not self.api._papers_due():
            return
        added, error = self.api._fetch_papers()
        if error and not added:
            self._papers_retry_at = time.monotonic() + 1800
            return
        if added:
            text = self.api._json_setting_text("papers_notify_text") or self._text("papers")
            self.icon.notify(text, self._text("papers_title").format(n=added))
            self.after_sync()

    def _check_update(self) -> None:
        if not self.api._update_due():
            return
        info = self.api._check_update()
        self.icon.update_menu()
        if info and info["version"] != self._update_notified:  # once per version per run
            self._update_notified = info["version"]
            self.icon.notify(self._text("update_body"), self._text("update_title").format(v=info["version"]))

    def _install_update(self) -> None:
        def run():
            try:
                self.api.install_update()
            except Exception:
                self.icon.notify(self._text("update_failed"), "Labmate")
        threading.Thread(target=run, daemon=True).start()

    def _check_reminders(self) -> None:
        minutes = self.api._setting("remind")
        if minutes == "off":
            return
        tasks, events = self.api._reminder_items()
        now = datetime.now()
        due = due_reminders(now, tasks, events, timedelta(minutes=int(minutes)), self._reminded)
        if not due:
            return
        self._reminded.update(key for key, _, _ in due)
        lines = [f"{start:%H:%M}  {title}" for _, title, start in due]
        if len(due) == 1:
            left = max(1, round((due[0][2] - now).total_seconds() / 60))
            title = self._text("soon").format(m=left)
        else:
            title = self._text("soon_many").format(n=len(due))
        self.icon.notify("\n".join(lines), title)

    def _sync_loop(self) -> None:
        """Calendar sync at start, every 5 minutes, and shortly after local edits."""
        while not self.quitting:
            self.api._sync_calendar()
            self.after_sync()
            if self._sync_wakeup.wait(timeout=300):
                self._sync_wakeup.clear()
                time.sleep(2)  # let a burst of edits settle into one sync

    def _weather_loop(self) -> None:
        while not self.quitting:
            self.api._refresh_weather()
            self.after_sync()
            time.sleep(1800)  # forecasts change a few times a day; 30 min is plenty

    def request_sync(self) -> None:
        self._sync_wakeup.set()

    def after_sync(self) -> None:
        """Pull-side changes (calendar edits, today's events) need a re-render."""
        self.refresh_icon()
        for w in (self.main, self.popup):
            try:
                w.evaluate_js("window.reloadData && reloadData()")
            except Exception:
                pass

    def pick_json_file(self) -> str | None:
        paths = self.main.create_file_dialog(webview.FileDialog.OPEN, file_types=("JSON (*.json)",))
        return paths[0] if paths else None

    def _on_main_closing(self):
        if self.quitting:
            return True
        # Closing the main window only hides it; the app lives on in the tray.
        threading.Thread(target=self.main.hide, daemon=True).start()
        return False

    # --- called from the tray and from Api ----------------------------------

    def _text(self, key: str) -> str:
        return TRAY_TEXT[self.api._setting("lang")][key]

    def refresh_icon(self) -> None:
        n = self.api._open_today()
        self.icon.icon = make_icon(n)
        self.icon.title = self._text("open").format(n=n) if n else self._text("clear")
        self.icon.update_menu()

    def toggle_popup(self) -> None:
        if self.popup_visible:
            self.hide_popup()
            return
        # Clicking the tray icon blurs (and hides) an open popup first; don't reopen it.
        if time.monotonic() - self.popup_hidden_at < 0.4:
            return
        self.popup.move(*_popup_position())
        self.popup_shown_at = time.monotonic()
        self.popup.show()
        self.popup_visible = True

    def popup_blurred(self) -> None:
        # Windows may refuse focus to a just-shown window (foreground lock), which
        # blurs it immediately; ignore that so the popup doesn't vanish on open.
        if time.monotonic() - self.popup_shown_at > 0.5:
            self.hide_popup()

    def quick_add(self) -> None:
        if not self.popup_visible:
            self.popup.move(*_popup_position())
            self.popup_shown_at = time.monotonic()
            self.popup.show()
            self.popup_visible = True
        self.popup.evaluate_js("focusQuickAdd()")

    def hide_popup(self) -> None:
        if not self.popup_visible:
            return
        self.popup_visible = False
        self.popup_hidden_at = time.monotonic()
        self.popup.hide()

    def show_main(self, task_id: int | None = None) -> None:
        self.hide_popup()
        self.main.show()
        self.main.restore()
        if task_id is not None:
            self.main.evaluate_js(f"focusTask({int(task_id)})")

    def quit_soon(self) -> None:
        threading.Timer(1.0, self.quit).start()

    def quit(self) -> None:
        self.quitting = True
        self.icon.stop()
        self.popup.destroy()
        self.main.destroy()
