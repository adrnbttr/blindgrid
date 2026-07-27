"""Constraints that live in the packaging metadata rather than in the code.

These are easy to change without noticing what they cost, which is exactly why
they are asserted here with the reason attached.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

import blindgrid

ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
PROJECT = PYPROJECT["project"]


def test_the_python_floor_stays_at_3_11() -> None:
    """Raising this drops iPad support, silently.

    a-Shell — the iOS terminal blindgrid installs into — ships Python 3.11 and
    nothing newer, and cannot install packages with compiled extensions. So
    3.11 is not a conservative default here, it is a hard ceiling imposed by a
    supported platform. If you raise it, say so in the README and drop the iPad
    instructions in the same commit.
    """
    assert PROJECT["requires-python"] == ">=3.11"


def test_every_dependency_stays_pure_python() -> None:
    """iOS cannot build C extensions, so nothing in the tree may need one.

    This lists what we depend on rather than inspecting wheels, which would
    need a network. Adding a dependency means checking it is pure Python and
    adding it here — a deliberate step, which is the point.
    """
    known_pure = {"typer", "rich", "questionary", "tomli-w"}
    declared = {
        requirement.split(">=")[0].split("[")[0].strip() for requirement in PROJECT["dependencies"]
    }
    assert declared == known_pure, (
        "a dependency changed: confirm it ships no compiled extension, or iOS "
        "and any platform without a compiler loses the tool"
    )


def test_the_version_is_declared_once_and_matches() -> None:
    """A version that disagrees with itself misreports what is installed."""
    assert blindgrid.__version__ == PROJECT["version"]


def test_the_readme_is_shipped() -> None:
    """PyPI renders it as the project page; without it the listing is blank."""
    assert PROJECT["readme"] == "README.md"
    assert (ROOT / "README.md").is_file()


def test_the_example_config_reaches_the_wheel() -> None:
    """`config init` reads it from the installed package, not the checkout."""
    force_include = PYPROJECT["tool"]["hatch"]["build"]["targets"]["wheel"]["force-include"]
    assert force_include["config.example.toml"] == "blindgrid/data/config.example.toml"


def test_both_entry_points_exist() -> None:
    """The console script for normal use, the module for iOS."""
    assert PROJECT["scripts"]["blindgrid"] == "blindgrid.cli:app"
    assert (ROOT / "src" / "blindgrid" / "__main__.py").is_file()
