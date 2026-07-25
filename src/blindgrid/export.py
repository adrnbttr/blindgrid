"""Markdown export of a plan.

The export file is overwritten on every run, on purpose. Keeping a history of
past grids invites comparing them against results, and comparing them invites
looking for a pattern in independent events.
"""

from __future__ import annotations

import calendar
from pathlib import Path

from blindgrid.models import Grid, Plan
from blindgrid.render import DISCLAIMER, format_money


def _numbers(grids: tuple[Grid, ...]) -> str:
    return " · ".join(" ".join(str(number) for number in grid.numbers) for grid in grids)


def to_markdown(plan: Plan) -> str:
    """Render ``plan`` as a standalone Markdown document."""
    month_name = calendar.month_name[plan.month]
    lines = [
        f"# Lottery plan — {month_name} {plan.year}",
        "",
        f"*{DISCLAIMER}*",
        "",
        "## Draws",
        "",
    ]

    if plan.draws:
        lines += [
            "| Date | Day | Lottery | Numbers | Cost |",
            "| --- | --- | --- | --- | ---: |",
        ]
        lines += [
            f"| {draw.draw_date.isoformat()} | {draw.weekday_name} | {draw.lottery.label} "
            f"| {_numbers(draw.grids)} "
            f"| {format_money(draw.cost, draw.lottery.currency)} |"
            for draw in plan.draws
        ]
    else:
        lines.append("No draw could be planned with this budget.")

    lines += [
        "",
        "## Budget allocation",
        "",
        "| Lottery | Weight | Allocated | Committed | Grids | Unused |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    lines += [
        f"| {a.lottery.label} | {a.lottery.weight:g} "
        f"| {format_money(a.share, a.lottery.currency)} "
        f"| {format_money(a.committed, a.lottery.currency)} "
        f"| {a.grid_count} "
        f"| {format_money(a.remainder, a.lottery.currency)} |"
        for a in plan.allocations
    ]

    annotations = [(a.lottery.label, a.note) for a in plan.allocations if a.note]
    if annotations:
        lines += ["", "### Notes", ""]
        lines += [f"- **{label}**: {note}" for label, note in annotations]

    lines += [
        "",
        "## Totals",
        "",
        f"- Budget: **{format_money(plan.budget, plan.currency)}**",
        f"- Committed: **{format_money(plan.total_committed, plan.currency)}**",
        f"- Unspent: **{format_money(plan.unspent, plan.currency)}**",
        "",
    ]
    return "\n".join(lines)


def export_plan(plan: Plan, path: Path) -> Path:
    """Write ``plan`` to ``path``, replacing any previous export."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(to_markdown(plan), encoding="utf-8")
    return path
