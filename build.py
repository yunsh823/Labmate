"""Build the Windows app into dist/ToDoList/ (one folder, ToDoList.exe inside).

    python build.py

If %APPDATA%/ToDoList/client_secret.json exists, it is shipped inside the app so
people who install it can connect Google Calendar without importing a file.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

import googleapiclient
import PyInstaller.__main__

from todolist import __version__
from todolist.db import data_dir
from todolist.desktop import make_icon

ROOT = Path(__file__).parent
BUILD = ROOT / "build"
RESOURCES = ROOT / "todolist" / "resources"


def main() -> None:
    BUILD.mkdir(exist_ok=True)
    icon = BUILD / "app.ico"
    make_icon(size=256).save(icon, sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (256, 256)])

    client = data_dir() / "client_secret.json"
    if client.exists():
        RESOURCES.mkdir(exist_ok=True)
        shutil.copyfile(client, RESOURCES / "client_secret.json")
        print("Bundling Google OAuth client from", client)
    else:
        print("No OAuth client found; users will import one in Settings")

    # Only the Calendar API description; the full discovery cache is ~100 MB.
    calendar_doc = Path(googleapiclient.__file__).parent / "discovery_cache" / "documents" / "calendar.v3.json"
    sep = ";" if sys.platform == "win32" else ":"
    args = [
        str(ROOT / "run.py"),
        "--name", "ToDoList",
        "--windowed", "--noconfirm", "--clean",
        "--icon", str(icon),
        "--distpath", str(ROOT / "dist"), "--workpath", str(BUILD / "pyinstaller"), "--specpath", str(BUILD),
        "--add-data", f"{ROOT / 'todolist' / 'web'}{sep}todolist/web",
        "--add-data", f"{calendar_doc}{sep}googleapiclient/discovery_cache/documents",
        "--hidden-import", "pystray._win32",
        "--additional-hooks-dir", str(ROOT / "packaging" / "hooks"),
    ]
    if RESOURCES.exists():
        args += ["--add-data", f"{RESOURCES}{sep}todolist/resources"]
    # conda keeps these next to the interpreter in Library/bin, where PyInstaller doesn't look;
    # without them sqlite3, ctypes (tray, hotkey), tkinter (font list) and bz2 fail to import.
    conda_bin = Path(sys.prefix) / "Library" / "bin"
    for dll in ("sqlite3.dll", "ffi-8.dll", "tcl86t.dll", "tk86t.dll", "libbz2.dll"):
        if (conda_bin / dll).exists():
            args += ["--add-binary", f"{conda_bin / dll}{sep}."]
    PyInstaller.__main__.run(args)
    print(f"Built ToDoList {__version__} -> {ROOT / 'dist' / 'ToDoList' / 'ToDoList.exe'}")
    build_installer()


def build_installer() -> None:
    """Wrap dist/ToDoList into dist/ToDoList-Setup-<version>.exe with Inno Setup, if installed."""
    candidates = [Path(p) / "Inno Setup 6" / "ISCC.exe" for p in (
        os.environ.get("ProgramFiles(x86)", ""), os.environ.get("ProgramFiles", ""),
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs")]
    iscc = next((c for c in candidates if c.exists()), None) or shutil.which("iscc")
    if not iscc:
        print("Inno Setup not found; skipped the installer (dist/ToDoList still works as a folder)")
        return
    subprocess.run([str(iscc), f"/DAppVersion={__version__}", str(ROOT / "packaging" / "ToDoList.iss")], check=True)
    print(f"Installer -> {ROOT / 'dist' / f'ToDoList-Setup-{__version__}.exe'}")


if __name__ == "__main__":
    main()
