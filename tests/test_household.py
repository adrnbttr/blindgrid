"""Spreading a household's grids across draws."""

from __future__ import annotations

import random
from collections import Counter
from datetime import date

import pytest

from blindgrid.household import assign_dates

DATES = tuple(date(2026, 9, day) for day in (1, 4, 8, 11, 15, 18, 22, 25, 29))


@pytest.fixture
def generator() -> random.Random:
    return random.Random(4242)


def test_everyone_gets_what_they_asked_for(generator: random.Random) -> None:
    assigned = assign_dates([("Adrien", 4), ("Marie", 3)], DATES, generator)

    assert len(assigned["Adrien"]) == 4
    assert len(assigned["Marie"]) == 3


def test_nobody_plays_the_same_date_twice(generator: random.Random) -> None:
    assigned = assign_dates([("Adrien", 9), ("Marie", 9)], DATES, generator)

    for days in assigned.values():
        assert len(days) == len(set(days))


def test_dates_are_not_shared_while_free_ones_remain(generator: random.Random) -> None:
    """Nine dates, seven grids: no two people should land on the same draw."""
    assigned = assign_dates([("Adrien", 4), ("Marie", 3)], DATES, generator)

    used = [day for days in assigned.values() for day in days]
    assert len(used) == len(set(used))


def test_dates_are_shared_only_once_they_run_out(generator: random.Random) -> None:
    """Nine dates, twelve grids: exactly three dates end up shared."""
    assigned = assign_dates([("Adrien", 6), ("Marie", 6)], DATES, generator)

    used = Counter(day for days in assigned.values() for day in days)
    assert sum(used.values()) == 12
    assert len(used) == len(DATES)  # every date is used before any is reused
    assert sum(count - 1 for count in used.values()) == 3


def test_a_single_player_is_capped_by_the_dates(generator: random.Random) -> None:
    """Alone, you cannot play the same draw twice, so demand is capped."""
    assigned = assign_dates([("Adrien", 20)], DATES, generator)
    assert len(assigned["Adrien"]) == len(DATES)


def test_results_are_chronological(generator: random.Random) -> None:
    assigned = assign_dates([("Adrien", 5), ("Marie", 5)], DATES, generator)
    for days in assigned.values():
        assert list(days) == sorted(days)


def test_no_dates_means_nobody_plays(generator: random.Random) -> None:
    assert assign_dates([("Adrien", 3)], (), generator) == {"Adrien": ()}


def test_zero_demand_is_handled(generator: random.Random) -> None:
    assigned = assign_dates([("Adrien", 0), ("Marie", 2)], DATES, generator)
    assert assigned["Adrien"] == ()
    assert len(assigned["Marie"]) == 2


def test_scarce_dates_are_split_fairly() -> None:
    """With fewer dates than players want, no one player takes them all.

    Dealing in a fixed order would hand every free date to whoever is listed
    first. Over many runs each player should come out roughly even.
    """
    two_dates = DATES[:2]
    totals: Counter[str] = Counter()
    for seed in range(200):
        assigned = assign_dates([("Adrien", 1), ("Marie", 1)], two_dates, random.Random(seed))
        for name, days in assigned.items():
            totals[name] += len(days)

    assert totals["Adrien"] == totals["Marie"] == 200


def test_the_first_player_is_not_systematically_favoured() -> None:
    """One free date, two players: it should not always go to the same one."""
    winners: Counter[str] = Counter()
    for seed in range(200):
        assigned = assign_dates([("Adrien", 1), ("Marie", 1)], DATES[:1], random.Random(seed))
        for name, days in assigned.items():
            if days:
                winners[name] += 1

    # Both get the free date sometimes; the other shares it in phase two.
    assert winners["Adrien"] > 50
    assert winners["Marie"] > 50
