"""Assembling a month's plan from a budget.

This module wires the three independent steps together — allocate the money,
pick the dates, draw the numbers — and is the only place that knows the order
they run in.
"""

from __future__ import annotations

from collections.abc import Collection, Sequence
from dataclasses import replace
from datetime import date
from decimal import Decimal

from blindgrid.allocation import allocate
from blindgrid.filters import DEFAULT_ENABLED
from blindgrid.generator import draw_grids
from blindgrid.models import Allocation, Lottery, Plan, PlannedDraw, RandomSource
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
