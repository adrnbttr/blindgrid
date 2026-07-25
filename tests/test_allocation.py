"""Weighted budget allocation."""

from __future__ import annotations

from dataclasses import replace
from decimal import Decimal

import pytest

from blindgrid.allocation import allocate
from blindgrid.models import Lottery


def test_shares_are_proportional_to_weights(lotteries: tuple[Lottery, ...]) -> None:
    allocations = allocate(Decimal("40.00"), lotteries)
    shares = {a.lottery.label: a.share for a in allocations}

    # Weights 1.0 / 1.0 / 0.4 over 40.00 give 16.66 / 16.66 / 6.66.
    assert shares["EuroMillions"] == shares["Loto"]
    assert shares["EuroMillions"] == Decimal("16.66")
    assert shares["EuroDreams"] == Decimal("6.66")


def test_shares_never_exceed_the_budget(lotteries: tuple[Lottery, ...]) -> None:
    for raw in ("0.15", "3.33", "10.00", "37.77", "100.00"):
        budget = Decimal(raw)
        allocations = allocate(budget, lotteries)
        assert sum(a.share for a in allocations) <= budget


def test_committed_never_exceeds_the_share(lotteries: tuple[Lottery, ...]) -> None:
    for a in allocate(Decimal("27.50"), lotteries):
        assert a.committed <= a.share
        assert a.remainder >= 0


def test_zero_weight_is_excluded_but_reported(lotteries: tuple[Lottery, ...]) -> None:
    disabled = tuple(
        replace(lot, weight=0.0) if lot.label == "EuroDreams" else lot for lot in lotteries
    )
    allocations = {a.lottery.label: a for a in allocate(Decimal("40.00"), disabled)}

    assert allocations["EuroDreams"].share == Decimal("0.00")
    assert allocations["EuroDreams"].grid_count == 0
    assert allocations["EuroDreams"].is_skipped
    assert "weight is 0" in allocations["EuroDreams"].note

    # The freed weight goes to the remaining lotteries, which now split evenly.
    assert allocations["EuroMillions"].share == Decimal("20.00")
    assert allocations["Loto"].share == Decimal("20.00")


def test_every_weight_zero_disables_everything(lotteries: tuple[Lottery, ...]) -> None:
    disabled = tuple(replace(lot, weight=0.0) for lot in lotteries)
    allocations = allocate(Decimal("40.00"), disabled)

    assert all(a.is_skipped for a in allocations)
    assert sum(a.committed for a in allocations) == 0


def test_insufficient_share_is_reported_not_absorbed(
    euromillions: Lottery, eurodreams: Lottery
) -> None:
    # 5.00 split 1.0 / 0.4 leaves EuroDreams with 1.42, below its 2.50 grid.
    granted = allocate(Decimal("5.00"), (euromillions, eurodreams))
    allocations = {a.lottery.label: a for a in granted}

    assert allocations["EuroDreams"].grid_count == 0
    assert "below the 2.50 grid price" in allocations["EuroDreams"].note

    # The skipped share must not be handed to the other lottery.
    assert allocations["EuroMillions"].share == Decimal("3.57")
    assert allocations["EuroMillions"].grid_count == 1


def test_remainder_is_not_redistributed(loto: Lottery) -> None:
    # 10.00 buys four 2.20 grids, and 1.20 is deliberately left over.
    (allocation,) = allocate(Decimal("10.00"), (loto,))
    assert allocation.grid_count == 4
    assert allocation.committed == Decimal("8.80")
    assert allocation.remainder == Decimal("1.20")


@pytest.mark.parametrize("budget", ["0.01", "1.00", "2.19"])
def test_budget_below_any_grid_price_plans_nothing(budget: str, loto: Lottery) -> None:
    (allocation,) = allocate(Decimal(budget), (loto,))
    assert allocation.grid_count == 0
    assert allocation.is_skipped
