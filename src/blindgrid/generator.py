"""Drawing numbers from a cryptographically secure source.

Every number this tool produces comes from :class:`secrets.SystemRandom`,
which draws from the operating system's entropy pool. The :mod:`random`
module is never imported anywhere in the package: its Mersenne Twister is
seedable and reproducible, which is a liability here rather than a feature.

There is deliberately no seed option and no deterministic mode. Reproducible
lottery numbers would be a way to reintroduce exactly the human structure the
filters remove.
"""

from __future__ import annotations

from collections.abc import Collection
from secrets import SystemRandom

from blindgrid.errors import GridGenerationError
from blindgrid.filters import DEFAULT_ENABLED, accepts, active_rules
from blindgrid.models import Grid, Lottery, Pool, RandomSource

# Rejection sampling is cheap, but it must not be able to spin forever. With
# the shipped rules the acceptance rate stays well above 30% on realistic
# pools, so reaching this cap means the rule set is over-constrained for that
# pool and the user needs to hear about it.
MAX_ATTEMPTS = 500


def system_rng() -> RandomSource:
    """The CSPRNG used everywhere in production."""
    return SystemRandom()


def draw_pool(
    pool: Pool,
    rng: RandomSource,
    enabled: Collection[str] = DEFAULT_ENABLED,
) -> tuple[int, ...]:
    """Draw one set of numbers for ``pool``, retrying until filters accept it.

    Raises :class:`GridGenerationError` if no acceptable set turns up within
    :data:`MAX_ATTEMPTS`, rather than looping indefinitely.
    """
    for _ in range(MAX_ATTEMPTS):
        numbers = tuple(sorted(rng.sample(pool.population, pool.count)))
        if accepts(numbers, pool, enabled):
            return numbers

    rules = ", ".join(rule.name for rule in active_rules(pool, enabled)) or "none"
    raise GridGenerationError(
        f"No valid combination for pool {pool.name!r} ({pool.count} from {pool.maximum}) "
        f"after {MAX_ATTEMPTS} attempts. Active filters: {rules}. "
        f"Disable one of them under [filters] in your config."
    )


def draw_grids(
    lottery: Lottery,
    rng: RandomSource,
    enabled: Collection[str] = DEFAULT_ENABLED,
) -> tuple[Grid, ...]:
    """Draw one grid for ``lottery``: one set of numbers per pool."""
    return tuple(
        Grid(pool_name=pool.name, numbers=draw_pool(pool, rng, enabled)) for pool in lottery.pools
    )
