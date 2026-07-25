"""Planning a month for several people."""

from __future__ import annotations

import random
from collections import Counter
from datetime import date
from decimal import Decimal

import pytest

from blindgrid.models import Lottery, Player
from blindgrid.plan import build_household_plan


@pytest.fixture
def adrien() -> Player:
    return Player(
        name="Adrien",
        max_monthly_budget=Decimal("40.00"),
        weights={"EuroMillions": 1.0, "Loto": 1.0, "EuroDreams": 0.4},
    )


@pytest.fixture
def marie() -> Player:
    return Player(
        name="Marie",
        max_monthly_budget=Decimal("25.00"),
        weights={"Loto": 1.0, "EuroDreams": 1.0},
    )


def household(players, budgets, lotteries, rng, **kwargs):
    return build_household_plan(
        budgets=budgets,
        players=players,
        lotteries=lotteries,
        year=kwargs.pop("year", 2026),
        month=kwargs.pop("month", 9),
        rng=rng,
        **kwargs,
    )


def test_each_player_only_plays_their_own_lotteries(
    adrien: Player, marie: Player, lotteries: tuple[Lottery, ...], rng: random.Random
) -> None:
    plan = household(
        (adrien, marie), {"Adrien": Decimal("40"), "Marie": Decimal("25")}, lotteries, rng
    )

    played = {(d.player, d.lottery.label) for d in plan.draws}
    assert ("Marie", "EuroMillions") not in played
    assert {label for who, label in played if who == "Marie"} <= {"Loto", "EuroDreams"}
    assert {label for who, label in played if who == "Adrien"} == {
        "EuroMillions",
        "Loto",
        "EuroDreams",
    }


def test_nobody_exceeds_their_own_budget(
    adrien: Player, marie: Player, lotteries: tuple[Lottery, ...], rng: random.Random
) -> None:
    budgets = {"Adrien": Decimal("40.00"), "Marie": Decimal("25.00")}
    plan = household((adrien, marie), budgets, lotteries, rng)

    for name, budget in budgets.items():
        assert plan.committed_by(name) <= budget
    assert plan.total_committed <= plan.budget


def test_one_persons_spending_does_not_touch_the_others_share(
    adrien: Player, marie: Player, lotteries: tuple[Lottery, ...], rng: random.Random
) -> None:
    """Marie's envelope must be identical whether Adrien plays big or small."""
    generous = household(
        (adrien, marie), {"Adrien": Decimal("40"), "Marie": Decimal("25")}, lotteries, rng
    )
    frugal = household(
        (adrien, marie), {"Adrien": Decimal("5"), "Marie": Decimal("25")}, lotteries, rng
    )

    shares = lambda plan: {  # noqa: E731
        a.lottery.label: a.share for a in plan.allocations if a.player == "Marie"
    }
    assert shares(generous) == shares(frugal)


def test_the_same_lottery_is_not_played_twice_on_a_day_when_dates_allow(
    adrien: Player, marie: Player, lotteries: tuple[Lottery, ...], rng: random.Random
) -> None:
    """September has room for everyone, so no draw should be doubled up."""
    plan = household(
        (adrien, marie), {"Adrien": Decimal("40"), "Marie": Decimal("25")}, lotteries, rng
    )
    assert plan.shared_dates() == ()


def test_draws_are_shared_rather_than_grids_dropped(
    adrien: Player, marie: Player, lotteries: tuple[Lottery, ...], rng: random.Random
) -> None:
    """When dates run short, both keep their grids and the date is shared."""
    eurodreams_only = tuple(lot for lot in lotteries if lot.label == "EuroDreams")
    both = (
        Player(name="Adrien", max_monthly_budget=Decimal("40"), weights={"EuroDreams": 1.0}),
        Player(name="Marie", max_monthly_budget=Decimal("40"), weights={"EuroDreams": 1.0}),
    )
    # September holds 8 EuroDreams draws; 15 EUR each buys 6 grids apiece.
    plan = household(both, {"Adrien": Decimal("15"), "Marie": Decimal("15")}, eurodreams_only, rng)

    assert len(plan.draws) == 12
    assert plan.shared_dates() != ()
    assert plan.committed_by("Adrien") == Decimal("15.00")
    assert plan.committed_by("Marie") == Decimal("15.00")

    counts = Counter((d.draw_date, d.player) for d in plan.draws)
    assert max(counts.values()) == 1  # still nobody plays one draw twice


def test_a_player_left_out_of_the_budgets_does_not_play(
    adrien: Player, marie: Player, lotteries: tuple[Lottery, ...], rng: random.Random
) -> None:
    plan = household((adrien, marie), {"Adrien": Decimal("40")}, lotteries, rng)

    assert plan.player_names == ("Adrien",)
    assert not any(d.player == "Marie" for d in plan.draws)
    assert plan.budget == Decimal("40.00")


def test_the_budget_shown_is_the_one_that_was_put_in(
    adrien: Player, marie: Player, lotteries: tuple[Lottery, ...], rng: random.Random
) -> None:
    """Shares round down, so summing them would understate what was committed."""
    plan = household(
        (adrien, marie), {"Adrien": Decimal("40.00"), "Marie": Decimal("25.00")}, lotteries, rng
    )

    assert plan.budget_of("Adrien") == Decimal("40.00")
    assert plan.budget_of("Marie") == Decimal("25.00")
    assert plan.budget == Decimal("65.00")


def test_a_household_plan_knows_it_is_one(
    adrien: Player, lotteries: tuple[Lottery, ...], rng: random.Random
) -> None:
    plan = household((adrien,), {"Adrien": Decimal("40")}, lotteries, rng)

    assert plan.is_household
    assert plan.player_names == ("Adrien",)
    assert all(d.player == "Adrien" for d in plan.draws)


def test_only_future_draws_are_planned(
    adrien: Player, marie: Player, lotteries: tuple[Lottery, ...], rng: random.Random
) -> None:
    cutoff = date(2026, 9, 20)
    plan = household(
        (adrien, marie),
        {"Adrien": Decimal("40"), "Marie": Decimal("25")},
        lotteries,
        rng,
        not_before=cutoff,
    )
    assert all(d.draw_date >= cutoff for d in plan.draws)
