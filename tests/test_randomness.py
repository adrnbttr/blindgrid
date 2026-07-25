"""A contract test: the package must never reach for a weak random source.

This is the one property of the tool that cannot be checked by looking at its
output. A plan generated from :func:`random.random` looks exactly like a plan
generated from the system entropy pool — until someone knows the seed.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

PACKAGE_ROOT = Path(__file__).resolve().parents[1] / "src" / "blindgrid"
SOURCE_FILES = sorted(PACKAGE_ROOT.rglob("*.py"))


def test_the_package_was_found() -> None:
    assert SOURCE_FILES, f"no source files under {PACKAGE_ROOT}"


@pytest.mark.parametrize("path", SOURCE_FILES, ids=lambda path: path.name)
def test_no_module_imports_random(path: Path) -> None:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            offending = [alias.name for alias in node.names if alias.name.split(".")[0] == "random"]
            assert not offending, f"{path.name}:{node.lineno} imports {offending[0]}"
        elif isinstance(node, ast.ImportFrom):
            module = (node.module or "").split(".")[0]
            assert module != "random", f"{path.name}:{node.lineno} imports from random"


def test_the_generator_uses_the_system_source() -> None:
    source = (PACKAGE_ROOT / "generator.py").read_text(encoding="utf-8")
    assert "from secrets import SystemRandom" in source


@pytest.mark.parametrize("path", SOURCE_FILES, ids=lambda path: path.name)
def test_no_seeding_entry_point_exists(path: Path) -> None:
    """No `--seed` option, anywhere. Reproducible draws are out of scope."""
    source = path.read_text(encoding="utf-8")
    assert "--seed" not in source
