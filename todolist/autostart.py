"""Start with Windows: an entry under HKCU\\...\\Run pointing at the installed exe.

The registry is the source of truth (the user can also toggle it in Task Manager),
so nothing is stored in the app's own settings.
"""

import sys

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
VALUE = "ToDoList"


def supported() -> bool:
    """Only the packaged app has a stable exe path worth registering."""
    return sys.platform == "win32" and bool(getattr(sys, "frozen", False))


def is_enabled(key: str = RUN_KEY) -> bool:
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key) as k:
            winreg.QueryValueEx(k, VALUE)
            return True
    except FileNotFoundError:
        return False


def set_enabled(on: bool, exe: str | None = None, key: str = RUN_KEY) -> None:
    import winreg
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key) as k:
        if on:
            winreg.SetValueEx(k, VALUE, 0, winreg.REG_SZ, f'"{exe or sys.executable}"')
        else:
            try:
                winreg.DeleteValue(k, VALUE)
            except FileNotFoundError:
                pass
