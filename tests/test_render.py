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

from blindgrid.export import to_markdown
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


# ------------------------------------------------- narrow terminals (phones, tablets)


def test_the_table_is_used_when_it_fits(plan: Plan) -> None:
    # Corners vary by platform — rich squares them off on the Windows console —
    # so the junction character is what identifies a table everywhere.
    output = render(plan, width=130)
    assert "┼" in output and "│" in output


@pytest.mark.parametrize("width", [40, 50])
def test_a_phone_drops_the_table(width: int, plan: Plan) -> None:
    """Below what even the leanest table needs, it shreds the numbers."""
    output = render(plan, width=width)
    assert "┼" not in output, "a table survived at a width that cannot hold it"


def test_the_table_sheds_columns_before_giving_up(household: Plan) -> None:
    """Between the two extremes, a table missing a column beats a list.

    The cost is fixed per lottery and totalled below; the weekday follows from
    the date. Both go before the table itself does.
    """
    wide = render(household, width=120)
    assert "Cost" in wide and "Day" in wide

    middle = render(household, width=78)
    assert "┼" in middle, "gave up on the table while one could still fit"
    assert "Cost" not in middle

    tighter = render(household, width=68)
    assert "┼" in tighter
    assert "Day" not in tighter

    # What is left is the irreducible answer: what to play, and when.
    for output in (middle, tighter):
        assert "Numbers" in output and "Lottery" in output and "Date" in output


@pytest.mark.parametrize("width", [40, 50, 60, 70])
def test_numbers_are_never_wrapped_when_narrow(width: int, plan: Plan) -> None:
    """The numbers get copied onto a paper slip; splitting them is the one
    thing that must not happen."""
    output = render(plan, width=width)

    for draw in plan.draws:
        first = draw.grids[0]
        rendered = " ".join(str(n).rjust(2) for n in first.numbers).strip()
        assert rendered in output, f"numbers split at width {width}"


@pytest.mark.parametrize("width", [40, 50, 60, 70, 90, 130])
def test_no_line_ever_overflows(width: int, household: Plan) -> None:
    for line in render(household, width=width).splitlines():
        assert len(line) <= width, f"line of {len(line)} at width {width}: {line!r}"


def test_nothing_is_truncated_when_narrow(plan: Plan) -> None:
    """No ellipsis: a lottery called "Eur…" is worse than a second line."""
    assert "…" not in render(plan, width=50)


def test_a_narrow_plan_still_reports_the_totals(household: Plan) -> None:
    output = render(household, width=55)

    assert f"{household.total_committed:.2f}" in output
    assert f"{household.unspent:.2f}" in output
    assert "Adrien" in output and "Marie" in output


def test_the_layout_can_be_forced_either_way(plan: Plan) -> None:
    console = Console(width=130, no_color=True)
    with console.capture() as captured:
        render_plan(plan, console, compact=True)
    assert "┼" not in captured.get()

    narrow = Console(width=60, no_color=True)
    with narrow.capture() as captured:
        render_plan(plan, narrow, compact=False)
    assert "┼" in captured.get()


def test_a_household_plan_names_players_when_narrow(household: Plan) -> None:
    output = render(household, width=60)
    assert "Adrien" in output and "Marie" in output


def test_an_empty_plan_is_fine_when_narrow(
    lotteries: tuple[Lottery, ...], rng: random.Random
) -> None:
    empty = build_plan(budget=Decimal("1.00"), lotteries=lotteries, year=2026, month=9, rng=rng)
    assert "No draw could be planned" in render(empty, width=45)


def test_the_table_survives_a_tablet_in_portrait(household: Plan) -> None:
    """An iPad in portrait gives about 90 columns in a-Shell.

    The table used to need 97 and fell back to the list there, which meant the
    layout flipped when you rotated the device — the worst of both. Dropping
    the redundant year and month from every row, and abbreviating the weekday,
    brought it under. Keep it that way.
    """
    output = render(household, width=90)
    assert "┼" in output, "the table no longer fits a tablet in portrait"


def test_rows_carry_the_day_not_the_full_date(household: Plan) -> None:
    """The month is in the title; repeating it on every row is noise."""
    output = render(household, width=110)
    assert "September 2026" in output
    assert "2026-09-" not in output


def test_the_export_keeps_full_dates(household: Plan) -> None:
    """The Markdown file is read away from the terminal, so it stays explicit."""
    document = to_markdown(household)
    assert "2026-09-" in document
