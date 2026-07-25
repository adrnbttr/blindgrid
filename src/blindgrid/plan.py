"""Assembling a month's plan from a budget.

This module wires the independent steps together — allocate the money, pick
the dates, draw the numbers — and is the only place that knows the order they
run in.

Two entry points: :func:`build_plan` for one person, and
:func:`build_household_plan` when several people share a month and their draws
have to be spread out.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping, Sequence
from dataclasses import replace
from datetime import date
from decimal import Decimal

from blindgrid.allocation import allocate
from blindgrid.filters import DEFAULT_ENABLED
from blindgrid.generator import draw_grids
from blindgrid.household import assign_dates
from blindgrid.models import (
    Allocation,
    Lottery,
    Plan,
    PlannedDraw,
    Player,
    RandomSource,
    money,
)
from blindgrid.planner import draw_dates, select_draws


def build_plan(
    *,
    budget: Decimal,
    lotteries: Sequence[Lottery],
    year: int,
    month: int,
    rng: RandomSource,
    enabled_filters: Collection[str] = DEFAULT_ENABLED,
    not_before: date | None = None,
) -> Plan:
    """Produce the plan for one month, within ``budget``.

    The returned allocations are the ones actually applied: a lottery whose
    grid count was capped by the number of remaining draws comes back with the
    reduced count and a note explaining it.
    """
    allocations: list[Allocation] = []
    draws: list[PlannedDraw] = []

    for allocation in allocate(budget, lotteries):
        if allocation.is_skipped:
            allocations.append(allocation)
            continue

        candidates = draw_dates(allocation.lottery, year, month, not_before)
        if not candidates:
            allocations.append(
                replace(allocation, grid_count=0, note="no draw left in this period")
            )
            continue

        playable = min(allocation.grid_count, len(candidates))
        unplayed = allocation.grid_count - playable
        note = (
            None
            if not unplayed
            else (
                f"only {len(candidates)} draw(s) left in the period, "
                f"{unplayed} affordable grid(s) unplayed"
            )
        )

        for day in select_draws(candidates, playable, rng):
            draws.append(
                PlannedDraw(
                    draw_date=day,
                    lottery=allocation.lottery,
                    grids=draw_grids(allocation.lottery, rng, enabled_filters),
                )
            )

        allocations.append(replace(allocation, grid_count=playable, note=note))

    draws.sort(key=lambda entry: (entry.draw_date, entry.lottery.label))

    return Plan(
        year=year,
        month=month,
        budget=budget,
        allocations=tuple(allocations),
        draws=tuple(draws),
    )


def build_household_plan(
    *,
    budgets: Mapping[str, Decimal],
    players: Sequence[Player],
    lotteries: Sequence[Lottery],
    year: int,
    month: int,
    rng: RandomSource,
    enabled_filters: Collection[str] = DEFAULT_ENABLED,
    not_before: date | None = None,
) -> Plan:
    """Plan a month for several people at once.

    Each player's budget is allocated against their own weights, entirely
    independently — nobody's share is affected by what anyone else spends.
    Only the choice of dates is coordinated, so the household covers as many
    distinct draws as it can before any date is played twice.
    """
    # Allocate each player's own envelope first. Weights are per player, so the
    # global weight on a lottery is replaced by this player's own.
    granted: list[tuple[str, Allocation]] = []
    for player in players:
        budget = budgets.get(player.name)
        if budget is None:
            continue
        playable = tuple(
            replace(lottery, weight=player.weight_for(lottery))
            for lottery in lotteries
            if player.plays(lottery)
        )
        granted.extend(
            (player.name, replace(allocation, player=player.name))
            for allocation in allocate(budget, playable)
        )

    # Group what everyone wants, lottery by lottery, so dates can be shared out.
    demand: dict[str, list[tuple[str, int]]] = {}
    lottery_of: dict[str, Lottery] = {}
    for name, allocation in granted:
        if allocation.grid_count:
            demand.setdefault(allocation.lottery.label, []).append((name, allocation.grid_count))
            lottery_of[allocation.lottery.label] = allocation.lottery

    draws: list[PlannedDraw] = []
    played: dict[tuple[str, str], int] = {}
    dates_available: dict[str, int] = {}

    for label, wanted in demand.items():
        lottery = lottery_of[label]
        candidates = draw_dates(lottery, year, month, not_before)
        dates_available[label] = len(candidates)

        for name, days in assign_dates(wanted, candidates, rng).items():
            played[(name, label)] = len(days)
            draws.extend(
                PlannedDraw(
                    draw_date=day,
                    lottery=lottery,
                    grids=draw_grids(lottery, rng, enabled_filters),
                    player=name,
                )
                for day in days
            )

    allocations = [
        _reconcile(allocation, played.get((name, allocation.lottery.label), 0), dates_available)
        for name, allocation in granted
    ]

    draws.sort(key=lambda entry: (entry.draw_date, entry.lottery.label, entry.player or ""))

    return Plan(
        year=year,
        month=month,
        budget=money(sum(budgets.values(), Decimal("0"))),
        allocations=tuple(allocations),
        draws=tuple(draws),
        player_budgets=tuple(
            (player.name, budgets[player.name]) for player in players if player.name in budgets
        ),
    )


def _reconcile(
    allocation: Allocation,
    actually_played: int,
    dates_available: Mapping[str, int],
) -> Allocation:
    """Bring an allocation in line with the dates its player really got."""
    if actually_played == allocation.grid_count:
        return allocation

    available = dates_available.get(allocation.lottery.label, 0)
    if not available:
        return replace(allocation, grid_count=0, note="no draw left in this period")

    unplayed = allocation.grid_count - actually_played
    return replace(
        allocation,
        grid_count=actually_played,
        note=(
            f"only {available} draw(s) left in the period, {unplayed} affordable grid(s) unplayed"
        ),
    )
