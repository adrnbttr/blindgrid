"""Domain model: pools, lotteries, grids and the monthly plan.

Nothing here knows about a specific lottery. A game is described entirely by
configuration, and the code only ever manipulates pools of integers. Adding a
lottery from any country is a configuration change, never a code change.

Money is handled as :class:`~decimal.Decimal` throughout. Budgets are compared
against grid prices, and binary floating point would make a plan drift over or
under the ceiling by a fraction of a cent.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Protocol

CENTS = Decimal("0.01")

WEEKDAY_NAMES: tuple[str, ...] = (
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
)


def money(value: Decimal | float | int | str) -> Decimal:
    """Return ``value`` as a Decimal rounded to two places."""
    return Decimal(str(value)).quantize(CENTS, rounding=ROUND_HALF_UP)


class RandomSource(Protocol):
    """The slice of :class:`random.Random` this tool relies on.

    Declaring a protocol rather than importing :mod:`random` keeps that module
    out of the package entirely, so a weak generator cannot be reached by
    accident. Production code always passes a :class:`secrets.SystemRandom`.
    """

    def sample(self, population: Sequence[Any], k: int) -> list[Any]:
        """Return ``k`` distinct elements drawn from ``population``."""
        ...


@dataclass(frozen=True, slots=True)
class Pool:
    """A set of ``count`` distinct integers drawn from ``1..maximum``.

    A lottery is one or more pools: EuroMillions is a 5-from-50 pool plus a
    2-from-12 pool.
    """

    name: str
    count: int
    maximum: int

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("pool name must not be empty")
        if self.count < 1:
            raise ValueError(f"pool {self.name!r}: count must be at least 1")
        if self.maximum < self.count:
            raise ValueError(
                f"pool {self.name!r}: max ({self.maximum}) must be at least count ({self.count})"
            )

    @property
    def population(self) -> range:
        """The integers this pool draws from."""
        return range(1, self.maximum + 1)


@dataclass(frozen=True, slots=True)
class Lottery:
    """A game definition, read verbatim from configuration."""

    label: str
    currency: str
    price_per_grid: Decimal
    draw_days: frozenset[int]
    weight: float
    pools: tuple[Pool, ...]

    def __post_init__(self) -> None:
        if not self.label:
            raise ValueError("lottery label must not be empty")
        if self.price_per_grid <= 0:
            raise ValueError(f"{self.label}: price_per_grid must be positive")
        if self.weight < 0:
            raise ValueError(f"{self.label}: weight must not be negative")
        if not self.pools:
            raise ValueError(f"{self.label}: at least one pool is required")
        if not self.draw_days:
            raise ValueError(f"{self.label}: at least one draw day is required")

    @property
    def is_enabled(self) -> bool:
        """A lottery with ``weight = 0`` stays in config but is never played."""
        return self.weight > 0


@dataclass(frozen=True, slots=True)
class Grid:
    """The numbers drawn for one pool of one draw."""

    pool_name: str
    numbers: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class PlannedDraw:
    """One dated entry of the plan: a calendar date and the grid to play."""

    draw_date: date
    lottery: Lottery
    grids: tuple[Grid, ...]

    @property
    def cost(self) -> Decimal:
        """One planned draw is one grid, whatever the number of pools."""
        return self.lottery.price_per_grid

    @property
    def weekday_name(self) -> str:
        return WEEKDAY_NAMES[self.draw_date.weekday()].capitalize()


@dataclass(frozen=True, slots=True)
class Allocation:
    """What a lottery was granted, and what it actually used.

    ``share`` is the theoretical envelope from the weighting, ``committed`` is
    what the plan spends. The gap between the two is deliberate and shown to
    the user: leftover money is never redistributed.

    ``note`` carries the reason whenever those two differ for a structural
    reason — a share too small for a single grid, or fewer draws in the month
    than the share could pay for. It is always surfaced in the output rather
    than being silently absorbed.
    """

    lottery: Lottery
    share: Decimal
    grid_count: int
    note: str | None = None

    @property
    def is_skipped(self) -> bool:
        return self.grid_count == 0

    @property
    def committed(self) -> Decimal:
        return money(self.lottery.price_per_grid * self.grid_count)

    @property
    def remainder(self) -> Decimal:
        return money(self.share - self.committed)


@dataclass(frozen=True, slots=True)
class Plan:
    """The full result of a ``generate`` run."""

    year: int
    month: int
    budget: Decimal
    allocations: tuple[Allocation, ...]
    draws: tuple[PlannedDraw, ...]

    @property
    def total_committed(self) -> Decimal:
        return money(sum((d.cost for d in self.draws), Decimal("0")))

    @property
    def unspent(self) -> Decimal:
        return money(self.budget - self.total_committed)

    @property
    def currency(self) -> str:
        """The currency to display totals in.

        Mixing currencies in one plan is a configuration mistake rather than a
        supported feature, so the first allocation decides the label.
        """
        return self.allocations[0].lottery.currency if self.allocations else ""
