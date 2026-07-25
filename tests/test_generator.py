"""Grid generation: rejection sampling, small pools, and the attempt cap."""

from __future__ import annotations

import random

import pytest

from blindgrid.errors import GridGenerationError
from blindgrid.filters import DEFAULT_ENABLED, accepts
from blindgrid.generator import draw_grids, draw_pool, system_rng
from blindgrid.models import Lottery, Pool

SAMPLE_SIZE = 200


@pytest.mark.parametrize(
    "pool",
    [
        Pool("numbers", 5, 50),
        Pool("numbers", 5, 49),
        Pool("numbers", 6, 40),
        Pool("stars", 2, 12),
        Pool("lucky", 1, 10),
        Pool("powerball", 1, 26),
    ],
)
def test_no_generated_grid_violates_its_filters(pool: Pool, rng: random.Random) -> None:
    for _ in range(SAMPLE_SIZE):
        numbers = draw_pool(pool, rng)
        assert accepts(numbers, pool)


@pytest.mark.parametrize("pool", [Pool("numbers", 5, 50), Pool("lucky", 1, 10)])
def test_numbers_are_distinct_sorted_and_in_range(pool: Pool, rng: random.Random) -> None:
    for _ in range(SAMPLE_SIZE):
        numbers = draw_pool(pool, rng)
        assert len(numbers) == pool.count
        assert len(set(numbers)) == pool.count
        assert list(numbers) == sorted(numbers)
        assert all(1 <= number <= pool.maximum for number in numbers)


def test_small_pools_degrade_instead_of_failing(rng: random.Random) -> None:
    """A 1-from-5 pool satisfies no shape rule, and must still be drawable."""
    tiny = Pool("dream", 1, 5)
    for _ in range(SAMPLE_SIZE):
        assert len(draw_pool(tiny, rng)) == 1


def test_an_impossible_pool_fails_loudly(rng: random.Random) -> None:
    """3 from 3 can only ever be 1-2-3, which the consecutive rule rejects."""
    impossible = Pool("numbers", 3, 3)
    with pytest.raises(GridGenerationError) as caught:
        draw_pool(impossible, rng)

    message = str(caught.value)
    assert "max_consecutive" in message
    assert "[filters]" in message


def test_an_impossible_pool_succeeds_once_the_rule_is_disabled(rng: random.Random) -> None:
    impossible = Pool("numbers", 3, 3)
    without_consecutive = set(DEFAULT_ENABLED) - {"max_consecutive", "spread_decades"}
    assert draw_pool(impossible, rng, without_consecutive) == (1, 2, 3)


def test_one_grid_per_pool(euromillions: Lottery, rng: random.Random) -> None:
    grids = draw_grids(euromillions, rng)
    assert [grid.pool_name for grid in grids] == ["numbers", "stars"]
    assert len(grids[0].numbers) == 5
    assert len(grids[1].numbers) == 2


def test_output_varies_between_draws(euromillions: Lottery, rng: random.Random) -> None:
    seen = {draw_pool(euromillions.pools[0], rng) for _ in range(50)}
    assert len(seen) == 50


def test_the_system_source_produces_valid_grids(euromillions: Lottery) -> None:
    """The real CSPRNG path, not just the seeded test generator."""
    grids = draw_grids(euromillions, system_rng())
    for grid, pool in zip(grids, euromillions.pools, strict=True):
        assert accepts(grid.numbers, pool)
