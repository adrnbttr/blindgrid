"""Where blindgrid keeps its files, on each platform.

Two directories, kept apart on purpose:

* **config** — your ceiling, your lotteries, your players. Yours to edit, worth
  backing up, and never touched by an uninstall.
* **state** — the plan for the current month. Regenerable, machine-written,
  and of no interest to anyone but this tool.

Linux and the BSDs follow the XDG base directory spec. macOS follows it too
rather than using ``~/Library/Application Support``: this is a terminal tool
whose configuration people are expected to open in an editor, and
``~/.config`` is where that is looked for. Windows uses ``%APPDATA%`` for
config and ``%LOCALAPPDATA%`` for state, which is the local convention for the
same split — roaming for what follows the user, local for what does not.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

APP_NAME = "blindgrid"


def is_windows() -> bool:
    return sys.platform.startswith("win")


def _from_env(variable: str) -> Path | None:
    value = os.environ.get(variable)
    return Path(value).expanduser() if value else None


def config_dir() -> Path:
    """The directory holding ``config.toml``."""
    if is_windows():
        base = _from_env("APPDATA") or Path.home() / "AppData" / "Roaming"
        return base / APP_NAME
    return (_from_env("XDG_CONFIG_HOME") or Path.home() / ".config") / APP_NAME


def state_dir() -> Path:
    """The directory holding the current plan."""
    if is_windows():
        base = _from_env("LOCALAPPDATA") or Path.home() / "AppData" / "Local"
        return base / APP_NAME
    return (_from_env("XDG_STATE_HOME") or Path.home() / ".local" / "state") / APP_NAME
