"""Shared fixtures.

Tests use a seeded :class:`random.Random` so failures are reproducible. That
is a testing concern only: the package itself never imports :mod:`random`, and
``test_randomness.py`` enforces it.
"""

from __future__ import annotations

import random
from decimal import Decimal

import pytest

from blindgrid.models import Lottery, Pool

MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY, SATURDAY, SUNDAY = range(7)


@pytest.fixture
def rng() -> random.Random:
    return random.Random(20260725)


@pytest.fixture
def euromillions() -> Lottery:
    return Lottery(
        label="EuroMillions",
        currency="EUR",
        price_per_grid=Decimal("2.50"),
        draw_days=frozenset({TUESDAY, FRIDAY}),
        weight=1.0,
        pools=(Pool("numbers", 5, 50), Pool("stars", 2, 12)),
    )


@pytest.fixture
def loto() -> Lottery:
    return Lottery(
        label="Loto",
        currency="EUR",
        price_per_grid=Decimal("2.20"),
        draw_days=frozenset({MONDAY, WEDNESDAY, SATURDAY}),
        weight=1.0,
        pools=(Pool("numbers", 5, 49), Pool("lucky", 1, 10)),
    )


@pytest.fixture
def eurodreams() -> Lottery:
    return Lottery(
        label="EuroDreams",
        currency="EUR",
        price_per_grid=Decimal("2.50"),
        draw_days=frozenset({MONDAY, THURSDAY}),
        weight=0.4,
        pools=(Pool("numbers", 6, 40), Pool("dream", 1, 5)),
    )


@pytest.fixture
def lotteries(euromillions: Lottery, loto: Lottery, eurodreams: Lottery) -> tuple[Lottery, ...]:
    return (euromillions, loto, eurodreams)
