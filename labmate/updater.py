"""Update check against the project's GitHub Releases, and one-click install of a newer version."""

import hashlib
import json
import subprocess
import tempfile
import urllib.request
from pathlib import Path

from . import __version__

REPO = "yunsh823/Labmate"
LATEST_URL = f"https://api.github.com/repos/{REPO}/releases/latest"
USER_AGENT = f"Labmate/{__version__} (update check)"


def parse_version(text: str) -> tuple[int, ...]:
    """'v1.2.3' -> (1, 2, 3); anything unparsable -> ()."""
    try:
        return tuple(int(p) for p in text.strip().lstrip("vV").split("."))
    except ValueError:
        return ()


def _get_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.load(resp)


def latest(current: str = __version__) -> dict | None:
    """The newest release if it is newer than `current` and ships an installer; None otherwise."""
    rel = _get_json(LATEST_URL)
    version = rel.get("tag_name", "").lstrip("vV")
    if parse_version(version) <= parse_version(current):
        return None
    asset = next((a for a in rel.get("assets", [])
                  if a["name"].lower().endswith(".exe") and "setup" in a["name"].lower()), None)
    if not asset:
        return None
    return {"version": version, "url": asset["browser_download_url"], "size": asset["size"],
            "sha256": (asset.get("digest") or "").removeprefix("sha256:") or None}


def download(info: dict, folder: Path | None = None) -> Path:
    """Fetch the installer and check its size and (when GitHub provides one) SHA-256; ValueError if they differ."""
    folder = folder or Path(tempfile.mkdtemp(prefix="labmate-update-"))
    path = folder / f"Labmate-Setup-{info['version']}.exe"
    digest = hashlib.sha256()
    req = urllib.request.Request(info["url"], headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=60) as resp, open(path, "wb") as f:
        while chunk := resp.read(1 << 16):
            digest.update(chunk)
            f.write(chunk)
    if path.stat().st_size != info["size"] or (info["sha256"] and digest.hexdigest() != info["sha256"]):
        path.unlink(missing_ok=True)
        raise ValueError("corrupt")
    return path


def install(path: Path) -> None:
    """Run the installer silently: it closes this app, upgrades in place and starts the new version.

    !autostart keeps the installer from re-adding the startup entry; the app's own setting decides that.
    """
    subprocess.Popen([str(path), "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART", "/MERGETASKS=!autostart"],
                     close_fds=True)
