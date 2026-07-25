"""Spreading a household's grids across draws.

When several people play the same lottery in the same month, this decides who
plays which date. The rule is simple: use a free date before reusing one, so
the household covers as many different draws as it can.

**This does not improve anyone's odds.** Two grids are two independent chances
whether they sit on the same draw or on different ones, and the probability
that at least one wins is identical either way. What spreading does buy is
exposure to more distinct jackpots — some of which have rolled over — and the
certainty that two people in the same house are not holding near-duplicate
tickets for one draw.

When there are fewer dates than grids, dates are shared rather than grids
dropped. Losing a grid someone budgeted for, to satisfy a constraint that does
not change the odds, would be the wrong trade.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date

from blindgrid.models import RandomSource


def assign_dates(
    demand: Sequence[tuple[str, int]],
    dates: Sequence[date],
    rng: RandomSource,
) -> dict[str, tuple[date, ...]]:
    """Hand out ``dates`` to players according to ``demand``.

    ``demand`` pairs a player name with how many draws they can afford. The
    result maps each player to the dates they play, in chronological order.

    Free dates go first, dealt round-robin in a random order so that no player
    is systematically favoured when dates are scarce. Only once every date is
    taken does a second pass share them, and a player never receives the same
    date twice.
    """
    assigned: dict[str, list[date]] = {name: [] for name, _ in demand}
    if not dates:
        return {name: () for name, _ in demand}

    remaining = {name: count for name, count in demand if count > 0}
    if not remaining:
        return {name: () for name, _ in demand}

    # Phase one: every date used at most once.
    free = list(rng.sample(list(dates), len(dates)))
    order = list(rng.sample(list(remaining), len(remaining)))

    while free and remaining:
        for name in order:
            if name not in remaining:
                continue
            if not free:
                break
            assigned[name].append(free.pop())
            remaining[name] -= 1
            if not remaining[name]:
                del remaining[name]

    # Phase two: dates run out, so they are shared. Each player still draws
    # from the dates they do not already hold, so nobody plays one twice.
    for name, still_needed in remaining.items():
        available = [day for day in dates if day not in assigned[name]]
        take = min(still_needed, len(available))
        assigned[name].extend(rng.sample(available, take))

    return {name: tuple(sorted(days)) for name, days in assigned.items()}
