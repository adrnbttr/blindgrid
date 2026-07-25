"""End-to-end plan assembly, and the one invariant that must never break."""

from __future__ import annotations

import random
from dataclasses import replace
from datetime import date
from decimal import Decimal

import pytest

from blindgrid.models import Lottery
from blindgrid.plan import build_plan


def _plan(budget: str, lotteries: tuple[Lottery, ...], rng: random.Random, **kwargs: object):
    return build_plan(
        budget=Decimal(budget),
        lotteries=lotteries,
        year=kwargs.pop("year", 2026),
        month=kwargs.pop("month", 9),
        rng=rng,
        **kwargs,
    )


@pytest.mark.parametrize("budget", ["2.20", "5.00", "13.37", "20.00", "40.00", "99.99", "250.00"])
def test_a_plan_never_exceeds_its_budget(
    budget: str, lotteries: tuple[Lottery, ...], rng: random.Random
) -> None:
    plan = _plan(budget, lotteries, rng)
    assert plan.total_committed <= plan.budget
    assert plan.unspent >= 0


def test_committed_matches_the_draws(lotteries: tuple[Lottery, ...], rng: random.Random) -> None:
    plan = _plan("40.00", lotteries, rng)
    assert plan.total_committed == sum(draw.cost for draw in plan.draws)
    assert len(plan.draws) == sum(a.grid_count for a in plan.allocations)


def test_each_lottery_gets_exactly_its_grid_count(
    lotteries: tuple[Lottery, ...], rng: random.Random
) -> None:
    plan = _plan("40.00", lotteries, rng)
    for allocation in plan.allocations:
        played = [d for d in plan.draws if d.lottery.label == allocation.lottery.label]
        assert len(played) == allocation.grid_count
        assert all(d.draw_date.weekday() in allocation.lottery.draw_days for d in played)


def test_draws_are_chronological(lotteries: tuple[Lottery, ...], rng: random.Random) -> None:
    plan = _plan("40.00", lotteries, rng)
    dates = [draw.draw_date for draw in plan.draws]
    assert dates == sorted(dates)


def test_a_lottery_is_capped_by_the_draws_available(
    eurodreams: Lottery, rng: random.Random
) -> None:
    """A budget larger than the month can absorb must not invent extra draws."""
    plan = _plan("500.00", (eurodreams,), rng)
    (allocation,) = plan.allocations

    # September 2026 holds 8 EuroDreams draws: 4 Mondays and 4 Thursdays.
    assert allocation.grid_count == 8
    assert len(plan.draws) == 8
    assert "unplayed" in allocation.note
    assert plan.unspent > Decimal("400.00")


def test_one_draw_is_played_at_most_once(eurodreams: Lottery, rng: random.Random) -> None:
    plan = _plan("500.00", (eurodreams,), rng)
    dates = [draw.draw_date for draw in plan.draws]
    assert len(dates) == len(set(dates))


def test_a_month_without_draws_is_reported(loto: Lottery, rng: random.Random) -> None:
    sundays_only = replace(loto, draw_days=frozenset({6}))
    plan = _plan("40.00", (sundays_only,), rng, not_before=date(2026, 9, 28))

    # No Sunday falls between 28 and 30 September 2026.
    assert plan.draws == ()
    assert plan.allocations[0].note == "no draw left in this period"
    assert plan.total_committed == 0


def test_not_before_is_respected(lotteries: tuple[Lottery, ...], rng: random.Random) -> None:
    cutoff = date(2026, 9, 20)
    plan = _plan("40.00", lotteries, rng, not_before=cutoff)
    assert all(draw.draw_date >= cutoff for draw in plan.draws)


def test_a_disabled_lottery_is_never_played(
    lotteries: tuple[Lottery, ...], rng: random.Random
) -> None:
    disabled = tuple(replace(lot, weight=0.0) if lot.label == "Loto" else lot for lot in lotteries)
    plan = _plan("40.00", disabled, rng)
    assert not any(draw.lottery.label == "Loto" for draw in plan.draws)


def test_a_budget_below_every_grid_price_plans_nothing(
    lotteries: tuple[Lottery, ...], rng: random.Random
) -> None:
    plan = _plan("1.00", lotteries, rng)
    assert plan.draws == ()
    assert plan.total_committed == 0
    assert plan.unspent == Decimal("1.00")
    assert all(a.note for a in plan.allocations)
