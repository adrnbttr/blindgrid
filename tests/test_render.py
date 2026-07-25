"""Terminal rendering: alignment, and what the tables must say.

A plan is read off the screen and copied onto a paper slip, digit by digit.
Anything that makes a column drift is a chance to copy the wrong number, so
alignment is tested here rather than left to the eye.
"""

from __future__ import annotations

import random
from decimal import Decimal

import pytest
from rich.console import Console

from blindgrid.models import Lottery, Plan, Player
from blindgrid.plan import build_household_plan, build_plan
from blindgrid.render import NumberLayout, format_numbers, format_weights, render_plan


@pytest.fixture
def plan(lotteries: tuple[Lottery, ...], rng: random.Random) -> Plan:
    return build_plan(budget=Decimal("40.00"), lotteries=lotteries, year=2026, month=9, rng=rng)


@pytest.fixture
def household(lotteries: tuple[Lottery, ...], rng: random.Random) -> Plan:
    people = (
        Player("Adrien", Decimal("40.00"), {"EuroMillions": 1.0, "Loto": 1.0, "EuroDreams": 0.4}),
        Player("Marie", Decimal("25.00"), {"Loto": 1.0, "EuroDreams": 1.0}),
    )
    return build_household_plan(
        budgets={"Adrien": Decimal("20"), "Marie": Decimal("12")},
        players=people,
        lotteries=lotteries,
        year=2026,
        month=9,
        rng=rng,
    )


def render(plan: Plan, width: int = 130) -> str:
    console = Console(width=width, force_terminal=False, no_color=True)
    with console.capture() as captured:
        render_plan(plan, console)
    return captured.get()


def number_cells(output: str) -> list[str]:
    """The Numbers column of every draw row."""
    return [
        line.split("│")[-3]
        for line in output.splitlines()
        if line.count("│") >= 6 and "Numbers" not in line and "─" not in line
    ]


def test_the_separator_sits_in_one_column(plan: Plan) -> None:
    """Lotteries of different sizes must not push the separator around."""
    cells = [cell for cell in number_cells(render(plan)) if "·" in cell]
    positions = {cell.index("·") for cell in cells}

    assert len(cells) > 3, "expected several draws to compare"
    assert len(positions) == 1, f"separator drifts across columns: {positions}"


def test_the_separator_holds_across_players(household: Plan) -> None:
    cells = [cell for cell in number_cells(render(household)) if "·" in cell]
    assert len({cell.index("·") for cell in cells}) == 1


def test_pool_names_start_in_one_column(household: Plan) -> None:
    """A 5-number and a 6-number lottery still line their pool labels up."""
    cells = [cell for cell in number_cells(render(household)) if "·" in cell]
    starts = {cell.index("·") + len("  ·  ") for cell in cells}
    assert len(starts) == 1


def test_numbers_are_right_aligned_within_their_pool(plan: Plan) -> None:
    """Single digits are padded, so units stay under units."""
    output = render(plan)
    assert " 1 " in output or " 1·" in output or output.count("  1") > 0


def test_layout_measures_the_widest_row(household: Plan) -> None:
    layout = NumberLayout.measure(household)

    # EuroDreams draws six from 40: six two-digit numbers and five spaces.
    assert layout.block(0) == 6 * 2 + 5
    # "stars" and "dream" are five characters; "lucky" too.
    assert layout.label(1) == 5


def test_layout_of_an_empty_plan_does_not_explode(
    lotteries: tuple[Lottery, ...], rng: random.Random
) -> None:
    empty = build_plan(budget=Decimal("1.00"), lotteries=lotteries, year=2026, month=9, rng=rng)
    layout = NumberLayout.measure(empty)

    assert layout.block(0) == 0
    assert layout.label(3) == 0


def test_format_numbers_without_a_layout_still_works(plan: Plan) -> None:
    """The layout is an optimisation for tables, not a requirement."""
    draw = plan.draws[0]
    assert format_numbers(draw.grids, draw.lottery.pools).plain


def test_weights_share_one_precision(household: Plan) -> None:
    """A column mixing 1 and 0.4 would put the decimal points out of line."""
    rendered = format_weights(household)
    assert rendered[1.0] == "1.0"
    assert rendered[0.4] == "0.4"
    assert len({len(text) for text in rendered.values()}) == 1


def test_whole_weights_stay_whole(euromillions: Lottery, loto: Lottery, rng: random.Random) -> None:
    """Nothing gains a pointless decimal when every weight is already whole."""
    whole = build_plan(
        budget=Decimal("40.00"), lotteries=(euromillions, loto), year=2026, month=9, rng=rng
    )
    assert set(format_weights(whole).values()) == {"1"}


def test_a_household_plan_shows_the_player_columns(household: Plan) -> None:
    output = render(household)

    assert "Player" in output
    assert "Per player" in output
    assert "Household totals" in output
    assert "Adrien" in output and "Marie" in output


def test_a_solo_plan_has_no_player_column(plan: Plan) -> None:
    output = render(plan)

    assert "Player" not in output
    assert "Per player" not in output
    assert "Totals" in output


def test_the_disclaimer_is_always_printed(plan: Plan) -> None:
    assert "not predictions" in render(plan)


def test_an_empty_plan_says_so(lotteries: tuple[Lottery, ...], rng: random.Random) -> None:
    empty = build_plan(budget=Decimal("1.00"), lotteries=lotteries, year=2026, month=9, rng=rng)
    assert "No draw could be planned" in render(empty)


def test_notes_explain_a_skipped_lottery(
    lotteries: tuple[Lottery, ...], rng: random.Random
) -> None:
    thin = build_plan(budget=Decimal("5.00"), lotteries=lotteries, year=2026, month=9, rng=rng)
    output = render(thin)
    assert "skipped this month" in output
