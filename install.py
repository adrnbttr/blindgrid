"""blindgrid installer for anywhere Python runs, iPad included.

    curl -sL https://raw.githubusercontent.com/adrnbttr/blindgrid/main/install.py | python3

The shell installer needs bash; the PowerShell one needs Windows. This one
needs only Python, which is what makes it the way in on iOS: a-Shell and iSH
ship Python and curl but no bash, and no git either — so it installs from a
source archive rather than a git URL.

It installs with pip into whatever environment is running it, writes a starter
configuration if there is none, and prints how to launch the tool from here.

It installs the published package from PyPI, and falls back to a source
archive from GitHub if that is unavailable — which covers a fresh checkout of
an unreleased change as well as a PyPI outage.

Options:
    --ref <branch|tag>   Install from GitHub at this ref instead of PyPI.
    --source <spec>      Install from somewhere else: a path, a URL.
    --no-config          Do not create a starter configuration.
    --check              Report what would happen, install nothing.
    --help               Show this.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

PACKAGE = "blindgrid"
REPO = "https://github.com/adrnbttr/blindgrid"
MIN_PYTHON = (3, 11)


# ----------------------------------------------------------------- presentation

_COLOUR = sys.stdout.isatty() and not os.environ.get("NO_COLOR")


def paint(text: str, code: str) -> str:
    return f"\033[{code}m{text}\033[0m" if _COLOUR else text


def step(message: str) -> None:
    print(f"{paint('·', '36')} {message}")


def ok(message: str) -> None:
    print(f"  {paint('✓', '32')} {message}")


def warn(message: str) -> None:
    print(f"  {paint('!', '33')} {message}")


def info(message: str) -> None:
    print(f"    {paint(message, '90')}")


def fail(message: str) -> None:
    print(f"\n  {paint('✗ ' + message, '31')}\n")
    raise SystemExit(1)


def banner() -> None:
    print()
    tagline = paint("· lottery grids from cryptographic randomness", "90")
    print(f"  {paint('blindgrid', '1')} {tagline}")
    print()


# -------------------------------------------------------------------- environment


def on_ios() -> bool:
    """Whether this is one of the iOS shells.

    a-Shell reports Darwin on an ARM device with no /usr/bin/sw_vers, and sets
    its own home under the app sandbox. Getting this right only changes the
    advice printed at the end, so a heuristic is fine.
    """
    if sys.platform != "darwin":
        return False
    return "a-Shell" in os.environ.get("SHELL", "") or not Path("/usr/bin/sw_vers").exists()


def launch_command() -> str:
    """How to start the tool once installed.

    A pip-installed console script does not always land on the PATH in the iOS
    shells, and the module form always works.
    """
    return "python3 -m blindgrid" if on_ios() else "blindgrid"


# ---------------------------------------------------------------------- installing


def has_pip() -> bool:
    result = subprocess.run(
        [sys.executable, "-m", "pip", "--version"], check=False, capture_output=True
    )
    return result.returncode == 0


def pip_install(source: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "pip", "install", "--upgrade", source],
        check=False,
        capture_output=True,
        text=True,
    )


def install(source: str, fallback: str = "") -> None:
    if not has_pip():
        warn("This Python has no pip.")
        info("On a-Shell, pip is built in — try updating the app.")
        info("Elsewhere: python3 -m ensurepip --upgrade")
        fail("Cannot install without pip.")

    step("Installing")
    info(source)
    try:
        completed = pip_install(source)
    except OSError as exc:
        fail(f"Could not run pip: {exc}")

    if completed.returncode != 0 and fallback:
        warn("not available there, trying the source archive")
        info(fallback)
        completed = pip_install(fallback)

    if completed.returncode != 0:
        for line in (completed.stderr or completed.stdout).strip().splitlines()[-6:]:
            info(line)
        fail("pip could not install blindgrid.")
    ok("installed")


def verify() -> None:
    step("Verifying")
    result = subprocess.run(
        [sys.executable, "-m", "blindgrid", "version"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        fail("Installed, but the command does not run.")
    ok(result.stdout.strip() or "blindgrid runs")


def write_config() -> None:
    step("Configuration")
    # Imported here: the package only exists once pip has run.
    from blindgrid import config, paths  # noqa: PLC0415

    target = paths.config_dir() / config.CONFIG_FILENAME
    if target.exists():
        ok(f"keeping the existing {target}")
        return

    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(config.example_toml(), encoding="utf-8")
    except OSError as exc:
        warn(f"could not write a starter config: {exc}")
        info(f"Run '{launch_command()} config init' yourself.")
        return

    ok(f"wrote a starter config to {target}")
    info("It ships three French games as examples. Check the prices, the draw")
    info("days and above all max_monthly_budget before you play.")


def farewell() -> None:
    command = launch_command()
    print()
    print(f"  {paint('Next:', '1')}")
    for suffix, description in (
        ("config show", "see what is configured"),
        ("player add", "add someone who plays"),
        ("generate", "plan this month"),
    ):
        left = paint(f"{command} {suffix}", "1")
        print(f"    {left:<38} {paint('· ' + description, '90')}")

    if on_ios():
        print()
        info("On a narrow screen the plan lays itself out as a list rather than")
        info("a table, so the numbers are never split across lines.")
        info("If prompts do not work in your shell, pass values as options:")
        info(f"  {command} generate --budget 30 --lottery Loto")

    print()
    print(f"  {paint('This tool predicts nothing. Lottery draws are independent events,', '90')}")
    print(f"  {paint('and no combination is more likely than another.', '90')}")
    print()
    print(f"  Docs: {REPO}")
    print()


# --------------------------------------------------------------------------- main


def main(argv: list[str]) -> None:
    if "--help" in argv or "-h" in argv:
        print(__doc__)
        return

    ref = "main"
    source = ""
    create_config = "--no-config" not in argv
    check_only = "--check" in argv

    for index, argument in enumerate(argv):
        if argument == "--ref" and index + 1 < len(argv):
            ref = argv[index + 1]
        elif argument == "--source" and index + 1 < len(argv):
            source = argv[index + 1]

    banner()

    step("Checking your environment")
    version = sys.version_info
    if version < MIN_PYTHON:
        warn(f"Python {version.major}.{version.minor} is too old.")
        info(f"blindgrid needs {MIN_PYTHON[0]}.{MIN_PYTHON[1]} or newer.")
        fail("Cannot continue.")
    ok(f"Python {version.major}.{version.minor}.{version.micro}")
    if on_ios():
        ok("iOS shell detected")

    # A source archive rather than git+: the iOS shells have no git.
    archive = f"{REPO}/archive/refs/heads/{ref}.zip"
    if source:
        wanted, fallback = source, ""
    elif "--ref" in argv:
        wanted, fallback = archive, ""
    else:
        wanted, fallback = PACKAGE, archive

    if check_only:
        info(f"would install: {wanted}")
        return

    install(wanted, fallback)
    verify()
    if create_config:
        write_config()
    farewell()


if __name__ == "__main__":
    main(sys.argv[1:])
