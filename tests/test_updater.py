import hashlib
import io

import pytest

from labmate import updater

PAYLOAD = b"installer bytes"


def release(tag, assets=None):
    if assets is None:
        assets = [{"name": f"Labmate-Setup-{tag.lstrip('v')}.exe", "size": len(PAYLOAD),
                   "browser_download_url": "https://example.invalid/setup.exe",
                   "digest": "sha256:" + hashlib.sha256(PAYLOAD).hexdigest()}]
    return {"tag_name": tag, "assets": assets}


def test_parse_version():
    assert updater.parse_version("v1.2.3") == (1, 2, 3)
    assert updater.parse_version("1.10.0") > updater.parse_version("1.9.9")
    assert updater.parse_version("nightly") == ()


def test_latest_only_reports_newer_releases(monkeypatch):
    monkeypatch.setattr(updater, "_get_json", lambda url: release("v1.0.1"))
    info = updater.latest("1.0.0")
    assert info["version"] == "1.0.1" and info["size"] == len(PAYLOAD)
    assert info["sha256"] == hashlib.sha256(PAYLOAD).hexdigest()
    assert updater.latest("1.0.1") is None
    assert updater.latest("1.1.0") is None


def test_latest_needs_an_installer(monkeypatch):
    monkeypatch.setattr(updater, "_get_json", lambda url: release("v2.0.0", assets=[]))
    assert updater.latest("1.0.0") is None


@pytest.mark.parametrize("body, ok", [(PAYLOAD, True), (b"tampered bytes!", False)])
def test_download_checks_the_digest(monkeypatch, tmp_path, body, ok):
    monkeypatch.setattr(updater, "_get_json", lambda url: release("v1.0.1"))
    monkeypatch.setattr(updater.urllib.request, "urlopen", lambda req, timeout: io.BytesIO(body))
    info = updater.latest("1.0.0")
    if ok:
        assert updater.download(info, tmp_path).read_bytes() == PAYLOAD
    else:
        with pytest.raises(ValueError):
            updater.download(info, tmp_path)
        assert not list(tmp_path.iterdir())  # the damaged file is not left behind
