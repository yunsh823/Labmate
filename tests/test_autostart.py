import sys

import pytest

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="Windows registry")

TEST_KEY = r"Software\LabmateTest\Run"  # scratch key, removed after the test


@pytest.fixture
def key():
    import winreg
    yield TEST_KEY
    for sub in (TEST_KEY, r"Software\LabmateTest"):
        try:
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, sub)
        except FileNotFoundError:
            pass


def test_toggle_writes_quoted_exe_path(key):
    import winreg
    from labmate import autostart
    assert not autostart.is_enabled(key)
    autostart.set_enabled(True, r"C:\Program Files\Labmate\Labmate.exe", key)
    assert autostart.is_enabled(key)
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key) as k:
        assert winreg.QueryValueEx(k, "Labmate")[0] == r'"C:\Program Files\Labmate\Labmate.exe"'
    autostart.set_enabled(False, key=key)
    autostart.set_enabled(False, key=key)  # turning off twice is fine
    assert not autostart.is_enabled(key)


def test_not_offered_when_running_from_source():
    from labmate import autostart
    assert autostart.supported() is False
