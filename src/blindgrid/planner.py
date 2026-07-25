"""Choosing which calendar dates to play.

The planner enumerates the real draw dates of a month, then picks a random
subset when the budget cannot cover them all. The subset must be random: a
regular pattern such as "every other Monday" is exactly the kind of human
structure this tool exists to remove, and it makes the schedule predictable to
anyone who knows the habit.
"""

from __future__ import annotations

import calendar
from collections.abc import Sequence
from datetime import date

from blindgrid.models import Lottery, RandomSource


def draw_dates(
    lottery: Lottery,
    year: int,
    month: int,
    not_before: date | None = None,
) -> tuple[date, ...]:
    """Every date in ``year``/``month`` that ``lottery`` draws on.

    ``not_before`` drops dates already past, which is what makes a plan
    generated mid-month actually playable.
    """
    _, days_in_month = calendar.monthrange(year, month)
    return tuple(
        day
        for day in (date(year, month, number) for number in range(1, days_in_month + 1))
        if day.weekday() in lottery.draw_days and (not_before is None or day >= not_before)
    )


def select_draws(
    dates: Sequence[date],
    count: int,
    rng: RandomSource,
) -> tuple[date, ...]:
    """Pick ``count`` dates at random from ``dates``, returned in order.

    Fewer candidates than ``count`` means every candidate is played; the caller
    is responsible for reporting the shortfall.
    """
    if count <= 0:
        return ()
    if count >= len(dates):
        return tuple(sorted(dates))
    return tuple(sorted(rng.sample(list(dates), count)))
