"""Anti-pattern filters and their degradation on small pools."""

from __future__ import annotations

import pytest

from blindgrid.filters import (
    DEFAULT_ENABLED,
    RULE_NAMES,
    accepts,
    active_rules,
    violations,
)
from blindgrid.models import Pool

BIG = Pool("numbers", 5, 50)
SMALL = Pool("dream", 1, 5)
STARS = Pool("stars", 2, 12)


def _names(pool: Pool) -> set[str]:
    return {rule.name for rule in active_rules(pool)}


def test_a_one_number_pool_has_no_active_rule() -> None:
    assert _names(SMALL) == set()
    assert accepts((3,), SMALL)


def test_a_two_number_pool_has_no_active_rule() -> None:
    """Two numbers cannot satisfy a spread or a parity mix without being forced."""
    assert _names(STARS) == set()
    assert accepts((1, 2), STARS)


def test_a_low_maximum_pool_skips_the_high_number_rule() -> None:
    low = Pool("numbers", 5, 20)
    assert "min_high_numbers" not in _names(low)
    assert "mixed_parity" in _names(low)


def test_a_large_pool_activates_every_rule() -> None:
    assert _names(BIG) == set(RULE_NAMES)


def test_rejects_too_few_high_numbers() -> None:
    assert "min_high_numbers" in violations((1, 5, 12, 20, 40), BIG)
    assert "min_high_numbers" not in violations((1, 5, 12, 35, 40), BIG)


def test_rejects_three_consecutive_numbers() -> None:
    assert "max_consecutive" in violations((11, 12, 13, 35, 44), BIG)
    assert "max_consecutive" not in violations((11, 12, 20, 35, 44), BIG)


def test_rejects_an_extreme_sum() -> None:
    assert "central_sum" in violations((1, 2, 3, 4, 50), BIG)
    assert "central_sum" in violations((44, 46, 47, 48, 50), BIG)
    assert "central_sum" not in violations((4, 19, 28, 37, 44), BIG)


def test_rejects_uniform_parity() -> None:
    assert "mixed_parity" in violations((2, 14, 24, 36, 48), BIG)
    assert "mixed_parity" in violations((1, 13, 23, 35, 47), BIG)
    assert "mixed_parity" not in violations((1, 14, 23, 36, 47), BIG)


def test_rejects_a_single_decade() -> None:
    assert "spread_decades" in violations((41, 42, 44, 46, 48), BIG)
    assert "spread_decades" not in violations((4, 19, 28, 37, 44), BIG)


def test_the_birthdate_pattern_is_rejected() -> None:
    """The combination this tool exists to avoid: five plausible birth dates."""
    assert not accepts((3, 7, 12, 19, 25), BIG)


def test_disabled_rules_are_not_applied() -> None:
    without_parity = set(DEFAULT_ENABLED) - {"mixed_parity"}
    assert "mixed_parity" not in violations((2, 14, 24, 36, 48), BIG, without_parity)


@pytest.mark.parametrize("count", range(1, 8))
def test_every_pool_size_is_handled(count: int) -> None:
    pool = Pool("numbers", count, 49)
    numbers = tuple(range(1, count + 1))
    assert isinstance(accepts(numbers, pool), bool)
