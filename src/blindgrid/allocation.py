"""Splitting a monthly budget across lotteries by weight.

Weights are relative shares of one envelope, not draw counts. A lottery with
``weight = 2.0`` receives twice the money of one at ``1.0``, whatever their
respective grid prices happen to be.

Two rules make the result honest rather than merely tidy:

* A share too small to buy a single grid skips that lottery for the month and
  says so. It never borrows from another lottery's share to round itself up.
* Leftover money inside a share is not redistributed and not spent. Total
  spend simply lands below budget. A tool that tried to consume the envelope
  exactly would be a tool that encourages spending.
"""

from __future__ import annotations

from collections.abc import Sequence
from decimal import ROUND_DOWN, Decimal

from blindgrid.models import CENTS, Allocation, Lottery


def _share_of(budget: Decimal, weight: float, total_weight: float) -> Decimal:
    """Return one lottery's slice of ``budget``, rounded down to the cent.

    Rounding down matters: with several lotteries, rounding to nearest could
    push the sum of the shares one cent above the budget, and the whole point
    of the ceiling is that it never moves.
    """
    ratio = Decimal(str(weight)) / Decimal(str(total_weight))
    return (budget * ratio).quantize(CENTS, rounding=ROUND_DOWN)


def allocate(budget: Decimal, lotteries: Sequence[Lottery]) -> tuple[Allocation, ...]:
    """Split ``budget`` across ``lotteries`` proportionally to their weights.

    Every lottery passed in comes back with an allocation, including the ones
    that end up with nothing, so the caller can report why.
    """
    total_weight = sum(lottery.weight for lottery in lotteries if lottery.is_enabled)

    if total_weight <= 0:
        return tuple(
            Allocation(
                lottery=lottery,
                share=Decimal("0.00"),
                grid_count=0,
                note="disabled (weight is 0)",
            )
            for lottery in lotteries
        )

    allocations = []
    for lottery in lotteries:
        if not lottery.is_enabled:
            allocations.append(
                Allocation(
                    lottery=lottery,
                    share=Decimal("0.00"),
                    grid_count=0,
                    note="disabled (weight is 0)",
                )
            )
            continue

        share = _share_of(budget, lottery.weight, total_weight)
        grid_count = int(share // lottery.price_per_grid)
        note = (
            None
            if grid_count
            else (
                f"share of {share} is below the {lottery.price_per_grid} grid price, "
                f"skipped this month"
            )
        )
        allocations.append(
            Allocation(lottery=lottery, share=share, grid_count=grid_count, note=note)
        )

    return tuple(allocations)
