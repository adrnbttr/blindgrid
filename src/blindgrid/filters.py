"""Anti-pattern filters applied to a freshly drawn set of numbers.

These rules do not improve the odds of winning — nothing can. They exist to
avoid the combinations humans pick on purpose, because a shared combination
means a shared jackpot. Choosing 1-2-3-4-5 has exactly the same probability of
being drawn as any other set, but thousands of players pick it.

Two design constraints follow from that:

* Rules are expressed relative to pool size, never against hardcoded lottery
  numbers, so a pool from any country behaves sensibly.
* The rule set stays small. Every additional rule shrinks the sample space,
  which pushes the output back toward a predictable subset — the opposite of
  what this tool is for.

Rules that cannot apply meaningfully to a small pool simply switch themselves
off: a 1-from-5 bonus pool has no room for a spread or a parity mix, so it is
drawn unfiltered rather than looping forever in search of an impossible set.
"""

from __future__ import annotations

from collections.abc import Callable, Collection
from dataclasses import dataclass
from itertools import pairwise

from blindgrid.models import Pool

# Above this value, numbers can no longer be a day of the month, which is where
# birthdate bias concentrates picks. This threshold is a fact about calendars,
# not about any particular lottery, so it is absolute rather than relative.
HIGH_NUMBER_THRESHOLD = 31
MIN_HIGH_NUMBERS = 2

# A run of three or more consecutive numbers reads as a deliberate pattern.
MAX_CONSECUTIVE_RUN = 2

# Accepted deviation from the mean sum, as a fraction of that mean.
CENTRAL_SUM_TOLERANCE = 0.30

# Below three numbers, shape rules either have no meaning or leave so few valid
# combinations that they would dominate the draw instead of trimming it.
MIN_COUNT_FOR_SHAPE_RULES = 3

DECADE_SIZE = 10


def _has_room_for_high_numbers(pool: Pool) -> bool:
    available = pool.maximum - HIGH_NUMBER_THRESHOLD
    return pool.count >= MIN_COUNT_FOR_SHAPE_RULES and available >= MIN_HIGH_NUMBERS


def _accepts_high_numbers(numbers: tuple[int, ...], _pool: Pool) -> bool:
    high = sum(1 for n in numbers if n > HIGH_NUMBER_THRESHOLD)
    return high >= MIN_HIGH_NUMBERS


def _is_shapeable(pool: Pool) -> bool:
    return pool.count >= MIN_COUNT_FOR_SHAPE_RULES


def _accepts_consecutive(numbers: tuple[int, ...], _pool: Pool) -> bool:
    longest = run = 1
    for previous, current in pairwise(numbers):
        run = run + 1 if current == previous + 1 else 1
        longest = max(longest, run)
    return longest <= MAX_CONSECUTIVE_RUN


def _accepts_central_sum(numbers: tuple[int, ...], pool: Pool) -> bool:
    mean = pool.count * (pool.maximum + 1) / 2
    return abs(sum(numbers) - mean) <= mean * CENTRAL_SUM_TOLERANCE


def _accepts_mixed_parity(numbers: tuple[int, ...], _pool: Pool) -> bool:
    odd = sum(1 for n in numbers if n % 2)
    return 0 < odd < len(numbers)


def _spans_several_decades(pool: Pool) -> bool:
    return pool.count >= MIN_COUNT_FOR_SHAPE_RULES and pool.maximum > DECADE_SIZE


def _accepts_spread(numbers: tuple[int, ...], _pool: Pool) -> bool:
    return len({(n - 1) // DECADE_SIZE for n in numbers}) > 1


@dataclass(frozen=True, slots=True)
class Rule:
    """One anti-pattern rule, with the pool sizes it makes sense for."""

    name: str
    description: str
    applies_to: Callable[[Pool], bool]
    accepts: Callable[[tuple[int, ...], Pool], bool]


RULES: tuple[Rule, ...] = (
    Rule(
        name="min_high_numbers",
        description=f"at least {MIN_HIGH_NUMBERS} numbers above {HIGH_NUMBER_THRESHOLD}",
        applies_to=_has_room_for_high_numbers,
        accepts=_accepts_high_numbers,
    ),
    Rule(
        name="max_consecutive",
        description=f"no more than {MAX_CONSECUTIVE_RUN} consecutive numbers",
        applies_to=_is_shapeable,
        accepts=_accepts_consecutive,
    ),
    Rule(
        name="central_sum",
        description="sum within a central range for the pool size",
        applies_to=_is_shapeable,
        accepts=_accepts_central_sum,
    ),
    Rule(
        name="mixed_parity",
        description="not all odd and not all even",
        applies_to=_is_shapeable,
        accepts=_accepts_mixed_parity,
    ),
    Rule(
        name="spread_decades",
        description="not every number inside a single decade",
        applies_to=_spans_several_decades,
        accepts=_accepts_spread,
    ),
)

RULE_NAMES: tuple[str, ...] = tuple(rule.name for rule in RULES)
DEFAULT_ENABLED: frozenset[str] = frozenset(RULE_NAMES)


def active_rules(pool: Pool, enabled: Collection[str] = DEFAULT_ENABLED) -> tuple[Rule, ...]:
    """Return the rules that are both enabled in config and viable for ``pool``."""
    return tuple(rule for rule in RULES if rule.name in enabled and rule.applies_to(pool))


def violations(
    numbers: tuple[int, ...],
    pool: Pool,
    enabled: Collection[str] = DEFAULT_ENABLED,
) -> tuple[str, ...]:
    """Return the names of the active rules ``numbers`` fails."""
    return tuple(
        rule.name for rule in active_rules(pool, enabled) if not rule.accepts(numbers, pool)
    )


def accepts(
    numbers: tuple[int, ...],
    pool: Pool,
    enabled: Collection[str] = DEFAULT_ENABLED,
) -> bool:
    """Whether ``numbers`` satisfies every active rule for ``pool``."""
    return not violations(numbers, pool, enabled)
