"""Per-platform locations for configuration and state.

These run on every platform, whatever the host actually is: the point is that
a Windows layout is produced on Windows and an XDG one everywhere else, and
neither can be checked by only ever testing on the machine you happen to use.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from blindgrid import paths


@pytest.fixture
def on_windows(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(paths.sys, "platform", "win32")


@pytest.fixture
def on_unix(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(paths.sys, "platform", "linux")


def test_windows_uses_appdata_for_config(
    on_windows: None, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("APPDATA", str(tmp_path / "Roaming"))
    assert paths.config_dir() == tmp_path / "Roaming" / "blindgrid"


def test_windows_uses_localappdata_for_state(
    on_windows: None, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """State is local, not roaming: a plan should not follow you between machines."""
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "Local"))
    assert paths.state_dir() == tmp_path / "Local" / "blindgrid"


def test_windows_falls_back_when_the_variables_are_missing(
    on_windows: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("APPDATA", raising=False)
    monkeypatch.delenv("LOCALAPPDATA", raising=False)

    assert paths.config_dir() == Path.home() / "AppData" / "Roaming" / "blindgrid"
    assert paths.state_dir() == Path.home() / "AppData" / "Local" / "blindgrid"


def test_windows_ignores_xdg(
    on_windows: None, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    monkeypatch.setenv("APPDATA", str(tmp_path / "Roaming"))
    assert paths.config_dir() == tmp_path / "Roaming" / "blindgrid"


def test_unix_follows_xdg(on_unix: None, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))

    assert paths.config_dir() == tmp_path / "config" / "blindgrid"
    assert paths.state_dir() == tmp_path / "state" / "blindgrid"


def test_unix_defaults_without_xdg(on_unix: None, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    monkeypatch.delenv("XDG_STATE_HOME", raising=False)

    assert paths.config_dir() == Path.home() / ".config" / "blindgrid"
    assert paths.state_dir() == Path.home() / ".local" / "state" / "blindgrid"


def test_an_empty_variable_is_treated_as_unset(
    on_unix: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", "")
    assert paths.config_dir() == Path.home() / ".config" / "blindgrid"


def test_config_and_state_never_collide(on_unix: None, monkeypatch: pytest.MonkeyPatch) -> None:
    """Uninstalling wipes state and keeps config, so they must not share a directory."""
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    monkeypatch.delenv("XDG_STATE_HOME", raising=False)
    assert paths.config_dir() != paths.state_dir()


def test_the_current_platform_is_usable() -> None:
    """Whatever this is running on, both directories resolve to absolute paths."""
    assert paths.config_dir().is_absolute()
    assert paths.state_dir().is_absolute()
