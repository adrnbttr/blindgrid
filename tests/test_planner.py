"""Calendar enumeration and random date selection."""

from __future__ import annotations

import random
from dataclasses import replace
from datetime import date

from blindgrid.models import Lottery
from blindgrid.planner import draw_dates, select_draws


def test_enumerates_every_matching_date(euromillions: Lottery) -> None:
    dates = draw_dates(euromillions, 2026, 9)

    # September 2026: Tuesdays 1, 8, 15, 22, 29 and Fridays 4, 11, 18, 25.
    assert dates == (
        date(2026, 9, 1),
        date(2026, 9, 4),
        date(2026, 9, 8),
        date(2026, 9, 11),
        date(2026, 9, 15),
        date(2026, 9, 18),
        date(2026, 9, 22),
        date(2026, 9, 25),
        date(2026, 9, 29),
    )


def test_stays_inside_the_month(loto: Lottery) -> None:
    for year, month in ((2026, 1), (2026, 2), (2026, 12), (2028, 2)):
        for day in draw_dates(loto, year, month):
            assert (day.year, day.month) == (year, month)


def test_handles_a_leap_february(loto: Lottery) -> None:
    # February 2028 has 29 days; the 28th is a Monday and the last Loto draw.
    february = draw_dates(loto, 2028, 2)
    assert february[-1] == date(2028, 2, 28)
    assert date(2028, 2, 29) not in february  # a Tuesday, not a Loto day

    saturdays = replace(loto, draw_days=frozenset({5}))
    assert draw_dates(saturdays, 2028, 2) == (
        date(2028, 2, 5),
        date(2028, 2, 12),
        date(2028, 2, 19),
        date(2028, 2, 26),
    )


def test_handles_a_31_day_month_ending_on_a_draw_day(euromillions: Lottery) -> None:
    # 31 March 2026 is a Tuesday: the last day of the month must be included.
    assert draw_dates(euromillions, 2026, 3)[-1] == date(2026, 3, 31)


def test_not_before_drops_past_dates(euromillions: Lottery) -> None:
    all_dates = draw_dates(euromillions, 2026, 9)
    remaining = draw_dates(euromillions, 2026, 9, not_before=date(2026, 9, 15))

    assert remaining == tuple(day for day in all_dates if day >= date(2026, 9, 15))
    assert date(2026, 9, 15) in remaining  # the cutoff day itself is still playable


def test_selection_returns_the_requested_count_in_order(
    euromillions: Lottery, rng: random.Random
) -> None:
    candidates = draw_dates(euromillions, 2026, 9)
    selected = select_draws(candidates, 4, rng)

    assert len(selected) == 4
    assert len(set(selected)) == 4
    assert list(selected) == sorted(selected)
    assert set(selected) <= set(candidates)


def test_selection_of_everything_keeps_everything(
    euromillions: Lottery, rng: random.Random
) -> None:
    candidates = draw_dates(euromillions, 2026, 9)
    assert select_draws(candidates, len(candidates), rng) == candidates
    assert select_draws(candidates, len(candidates) + 5, rng) == candidates


def test_selection_of_nothing_is_empty(euromillions: Lottery, rng: random.Random) -> None:
    candidates = draw_dates(euromillions, 2026, 9)
    assert select_draws(candidates, 0, rng) == ()
    assert select_draws(candidates, -1, rng) == ()


def test_selection_is_not_a_regular_pattern(euromillions: Lottery) -> None:
    """Repeated selections must not keep landing on the same dates.

    A planner that always picked the first n candidates, or every other one,
    would pass every test above. This one fails it.
    """
    candidates = draw_dates(euromillions, 2026, 9)
    generator = random.Random(7)
    seen = {select_draws(candidates, 4, generator) for _ in range(40)}

    assert len(seen) > 10
