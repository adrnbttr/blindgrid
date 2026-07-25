"""Keeping the current month's plan so it can be found again.

Once a month has been drawn, running ``generate`` again shows the same plan
rather than drawing a new one. That is not only a convenience for someone who
did not finish filling their grids in one sitting: a tool that redrew on every
run would let you reroll until the numbers looked right, which is precisely
the human bias the filters exist to remove.

**One file, replaced.** August's plan overwrites July's. This is a working
memory, not a history: months of past grids would invite comparing them
against results, and comparing invites looking for a pattern in independent
events.

The file is a self-contained snapshot — it carries the lottery definitions it
was drawn from, so editing your configuration afterwards never changes a plan
you already hold. It lives in the state directory rather than beside the
Markdown export, because the export path is relative to wherever you happened
to be standing and the plan has to be findable from anywhere.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

from blindgrid.errors import StoreError
from blindgrid.models import (
    WEEKDAY_NAMES,
    Allocation,
    Grid,
    Lottery,
    Plan,
    PlannedDraw,
    Pool,
    money,
)

SCHEMA_VERSION = 1
ENV_VAR = "BLINDGRID_STATE"
FILENAME = "plan.json"


@dataclass(frozen=True, slots=True)
class StoredPlan:
    """A plan read back from disk, with the moment it was drawn."""

    plan: Plan
    drawn_on: datetime


def default_path() -> Path:
    """Where the current plan is kept."""
    override = os.environ.get(ENV_VAR)
    if override:
        return Path(override).expanduser()
    state_home = os.environ.get("XDG_STATE_HOME") or str(Path.home() / ".local" / "state")
    return Path(state_home).expanduser() / "blindgrid" / FILENAME


def _lottery_to_dict(lottery: Lottery) -> dict[str, Any]:
    return {
        "label": lottery.label,
        "currency": lottery.currency,
        "price_per_grid": str(lottery.price_per_grid),
        "draw_days": [WEEKDAY_NAMES[day] for day in sorted(lottery.draw_days)],
        "weight": lottery.weight,
        "pools": [
            {"name": pool.name, "count": pool.count, "max": pool.maximum} for pool in lottery.pools
        ],
    }


def _lottery_from_dict(data: dict[str, Any]) -> Lottery:
    return Lottery(
        label=str(data["label"]),
        currency=str(data["currency"]),
        price_per_grid=money(data["price_per_grid"]),
        draw_days=frozenset(WEEKDAY_NAMES.index(day) for day in data["draw_days"]),
        weight=float(data["weight"]),
        pools=tuple(
            Pool(name=str(p["name"]), count=int(p["count"]), maximum=int(p["max"]))
            for p in data["pools"]
        ),
    )


def to_dict(plan: Plan, drawn_on: datetime) -> dict[str, Any]:
    """Render ``plan`` as the mapping written to disk."""
    return {
        "schema": SCHEMA_VERSION,
        "drawn_on": drawn_on.isoformat(timespec="seconds"),
        "year": plan.year,
        "month": plan.month,
        "budget": str(plan.budget),
        "allocations": [
            {
                "lottery": _lottery_to_dict(a.lottery),
                "share": str(a.share),
                "grid_count": a.grid_count,
                "note": a.note,
            }
            for a in plan.allocations
        ],
        "draws": [
            {
                "date": d.draw_date.isoformat(),
                "lottery": d.lottery.label,
                "grids": [{"pool": g.pool_name, "numbers": list(g.numbers)} for g in d.grids],
            }
            for d in plan.draws
        ],
    }


def from_dict(data: dict[str, Any]) -> StoredPlan:
    """Rebuild a plan from the mapping written by :func:`to_dict`."""
    schema = data.get("schema")
    if schema != SCHEMA_VERSION:
        raise StoreError(
            f"saved plan uses format version {schema!r}, this build expects {SCHEMA_VERSION}"
        )

    try:
        allocations = tuple(
            Allocation(
                lottery=_lottery_from_dict(entry["lottery"]),
                share=money(entry["share"]),
                grid_count=int(entry["grid_count"]),
                note=entry["note"],
            )
            for entry in data["allocations"]
        )
        by_label = {a.lottery.label: a.lottery for a in allocations}

        draws = tuple(
            PlannedDraw(
                draw_date=date.fromisoformat(entry["date"]),
                lottery=by_label[entry["lottery"]],
                grids=tuple(
                    Grid(pool_name=str(g["pool"]), numbers=tuple(int(n) for n in g["numbers"]))
                    for g in entry["grids"]
                ),
            )
            for entry in data["draws"]
        )

        plan = Plan(
            year=int(data["year"]),
            month=int(data["month"]),
            budget=money(data["budget"]),
            allocations=allocations,
            draws=draws,
        )
        drawn_on = datetime.fromisoformat(data["drawn_on"])
    except (KeyError, TypeError, ValueError) as exc:
        raise StoreError(f"saved plan is malformed ({exc})") from exc

    return StoredPlan(plan=plan, drawn_on=drawn_on)


def save(plan: Plan, path: Path | None = None, drawn_on: datetime | None = None) -> Path:
    """Write ``plan`` as the current plan, replacing any previous month."""
    target = path or default_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = to_dict(plan, drawn_on or datetime.now())
    target.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return target


def load(path: Path | None = None) -> StoredPlan | None:
    """Read the current plan, or ``None`` if none has been drawn yet.

    Raises :class:`StoreError` when a file is there but unreadable, so the
    caller can tell "nothing drawn yet" apart from "something is wrong".
    """
    target = path or default_path()
    if not target.exists():
        return None
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise StoreError(f"{target}: {exc}") from exc
    if not isinstance(data, dict):
        raise StoreError(f"{target}: expected an object at the top level")
    return from_dict(data)


def load_for(year: int, month: int, path: Path | None = None) -> StoredPlan | None:
    """The stored plan, but only if it covers ``year``/``month``."""
    stored = load(path)
    if stored is None or (stored.plan.year, stored.plan.month) != (year, month):
        return None
    return stored


def clear(path: Path | None = None) -> bool:
    """Delete the stored plan. Returns whether there was one."""
    target = path or default_path()
    if not target.exists():
        return False
    target.unlink()
    return True
