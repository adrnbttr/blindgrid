"""Command line behaviour, driven through Typer's runner."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from blindgrid import config, store
from blindgrid.cli import app

runner = CliRunner()


@pytest.fixture(autouse=True)
def wide_terminal(monkeypatch: pytest.MonkeyPatch) -> None:
    """Pin the render width.

    Rich wraps to the terminal, and pytest's temporary paths are long enough
    to be folded across lines at the default width, which would make these
    assertions depend on where the wrap lands.
    """
    monkeypatch.setenv("COLUMNS", "200")


@pytest.fixture
def workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A directory holding a valid config, with the CWD pointed at it.

    The saved plan is redirected here too, so tests never read or overwrite the
    plan of whoever is running them.
    """
    target = tmp_path / "config.toml"
    target.write_text(config.example_toml(), encoding="utf-8")
    monkeypatch.setenv(store.ENV_VAR, str(tmp_path / "state" / "plan.json"))
    monkeypatch.chdir(tmp_path)
    return tmp_path


def numbers_in(output: str) -> list[str]:
    """The drawn numbers, as they appear in the rendered table rows."""
    return [line.split("│")[4].strip() for line in output.splitlines() if line.count("│") > 4]


def test_generate_prints_a_plan_and_writes_the_export(workspace: Path) -> None:
    result = runner.invoke(
        app, ["generate", "--budget", "40", "--lottery", "Loto", "--month", "2026-09"]
    )

    assert result.exit_code == 0, result.output
    assert "Draws to play" in result.output
    assert "September 2026" in result.output
    assert (workspace / "plan.md").exists()


def test_no_export_leaves_the_file_alone(workspace: Path) -> None:
    result = runner.invoke(
        app,
        ["generate", "--budget", "40", "--lottery", "Loto", "-m", "2026-09", "--no-export"],
    )

    assert result.exit_code == 0
    assert not (workspace / "plan.md").exists()


def test_a_budget_above_the_ceiling_is_refused(workspace: Path) -> None:
    result = runner.invoke(app, ["generate", "--budget", "10000", "-l", "Loto", "-m", "2026-09"])

    assert result.exit_code == 1
    assert "exceeds the configured ceiling" in result.output


@pytest.mark.parametrize("budget", ["0", "-5", "abc"])
def test_an_invalid_budget_is_refused(budget: str, workspace: Path) -> None:
    result = runner.invoke(app, ["generate", "--budget", budget, "-l", "Loto", "-m", "2026-09"])
    assert result.exit_code == 1


def test_a_comma_decimal_separator_is_accepted(workspace: Path) -> None:
    result = runner.invoke(app, ["generate", "-b", "12,50", "-l", "Loto", "-m", "2026-09"])
    assert result.exit_code == 0


def test_an_unknown_lottery_lists_the_known_ones(workspace: Path) -> None:
    result = runner.invoke(app, ["generate", "-b", "10", "-l", "Powerball", "-m", "2026-09"])

    assert result.exit_code == 1
    assert "Unknown lottery" in result.output
    assert "EuroMillions" in result.output


def test_an_invalid_month_is_refused(workspace: Path) -> None:
    result = runner.invoke(app, ["generate", "-b", "10", "-l", "Loto", "-m", "2026-13"])

    assert result.exit_code == 1
    assert "YYYY-MM" in result.output


def test_a_missing_config_explains_itself(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv(config.ENV_VAR, str(tmp_path / "absent.toml"))
    result = runner.invoke(app, ["generate", "-b", "10", "-l", "Loto"])

    assert result.exit_code == 1
    assert "config init" in result.output


def test_config_init_creates_a_usable_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv(config.ENV_VAR, raising=False)

    assert runner.invoke(app, ["config", "init"]).exit_code == 0
    assert config.load(tmp_path / "config.toml").lotteries


def test_config_init_refuses_to_clobber(workspace: Path) -> None:
    result = runner.invoke(app, ["config", "init"])
    assert result.exit_code == 1
    assert "--force" in result.output

    assert runner.invoke(app, ["config", "init", "--force"]).exit_code == 0


def test_config_show_reports_the_active_file(workspace: Path) -> None:
    result = runner.invoke(app, ["config", "show"])
    assert result.exit_code == 0
    assert "config.toml" in result.output


def test_lottery_list_shows_every_definition(workspace: Path) -> None:
    result = runner.invoke(app, ["lottery", "list"])

    assert result.exit_code == 0
    for label in ("EuroMillions", "Loto", "EuroDreams"):
        assert label in result.output


def test_version_is_printed() -> None:
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "blindgrid" in result.output


# --------------------------------------------------------------- a month is drawn once


def test_running_twice_shows_the_same_numbers(workspace: Path) -> None:
    first = runner.invoke(app, ["generate", "-b", "30", "-l", "Loto", "-m", "2026-09"])
    second = runner.invoke(app, ["generate", "-b", "30", "-l", "Loto", "-m", "2026-09"])

    assert second.exit_code == 0
    assert "Plan already drawn on" in second.output
    assert numbers_in(first.output) == numbers_in(second.output)


def test_the_second_run_ignores_a_different_budget(workspace: Path) -> None:
    """The month is settled. Changing the arguments must not reroll it."""
    first = runner.invoke(app, ["generate", "-b", "10", "-l", "Loto", "-m", "2026-09"])
    second = runner.invoke(app, ["generate", "-b", "40", "-l", "EuroMillions", "-m", "2026-09"])

    assert numbers_in(first.output) == numbers_in(second.output)
    assert "10.00 EUR" in second.output


def test_force_draws_a_new_plan_and_says_so(workspace: Path) -> None:
    first = runner.invoke(app, ["generate", "-b", "30", "-l", "Loto", "-m", "2026-09"])
    forced = runner.invoke(app, ["generate", "-b", "30", "-l", "Loto", "-m", "2026-09", "--force"])

    assert forced.exit_code == 0
    assert "Replacing the plan drawn on" in forced.output
    assert "bias this tool removes" in forced.output
    assert numbers_in(first.output) != numbers_in(forced.output)


def test_a_different_month_is_drawn_fresh(workspace: Path) -> None:
    runner.invoke(app, ["generate", "-b", "30", "-l", "Loto", "-m", "2026-09"])
    october = runner.invoke(app, ["generate", "-b", "30", "-l", "Loto", "-m", "2026-10"])

    assert "Plan already drawn" not in october.output
    assert "October 2026" in october.output

    # The new month replaced the old one: no history piles up.
    assert store.load().plan.month == 10


def test_the_export_is_rewritten_when_a_plan_is_shown_again(workspace: Path) -> None:
    runner.invoke(app, ["generate", "-b", "30", "-l", "Loto", "-m", "2026-09"])
    (workspace / "plan.md").unlink()

    runner.invoke(app, ["generate", "-b", "30", "-l", "Loto", "-m", "2026-09"])
    assert (workspace / "plan.md").exists()


def test_a_corrupt_saved_plan_does_not_block_the_month(workspace: Path) -> None:
    state = Path(store.default_path())
    state.parent.mkdir(parents=True, exist_ok=True)
    state.write_text("{ not json", encoding="utf-8")

    result = runner.invoke(app, ["generate", "-b", "30", "-l", "Loto", "-m", "2026-09"])

    assert result.exit_code == 0
    assert "Ignoring the saved plan" in result.output
    assert "Draws to play" in result.output


def test_config_show_reports_the_saved_plan(workspace: Path) -> None:
    assert "none drawn yet" in runner.invoke(app, ["config", "show"]).output

    runner.invoke(app, ["generate", "-b", "30", "-l", "Loto", "-m", "2026-09"])
    assert "September 2026" in runner.invoke(app, ["config", "show"]).output
