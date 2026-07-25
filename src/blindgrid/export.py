"""Markdown export of a plan.

The export file is overwritten on every run, on purpose. Keeping a history of
past grids invites comparing them against results, and comparing them invites
looking for a pattern in independent events.
"""

from __future__ import annotations

from pathlib import Path

from blindgrid.i18n import month_name, t, weekday_name
from blindgrid.models import Grid, Plan
from blindgrid.render import format_money


def _numbers(grids: tuple[Grid, ...]) -> str:
    return " · ".join(" ".join(str(number) for number in grid.numbers) for grid in grids)


def to_markdown(plan: Plan) -> str:
    """Render ``plan`` as a standalone Markdown document."""
    month = month_name(plan.month)
    lines = [
        f"# {t('plan.title', month=month, year=plan.year)}",
        "",
        f"*{t('plan.disclaimer')}*",
        "",
        "## " + t("plan.column.numbers"),
        "",
    ]

    player_column = "Player | " if plan.is_household else ""
    player_rule = "--- | " if plan.is_household else ""

    if plan.draws:
        lines += [
            f"| {t('plan.column.date')} | {t('plan.column.day')} | {player_column}"
            f"{t('plan.column.lottery')} | {t('plan.column.numbers')} | {t('plan.column.cost')} |",
            f"| --- | --- | {player_rule}--- | --- | ---: |",
        ]
        lines += [
            f"| {draw.draw_date.isoformat()} | {weekday_name(draw.draw_date.weekday())} "
            f"| {draw.player + ' | ' if plan.is_household else ''}{draw.lottery.label} "
            f"| {_numbers(draw.grids)} "
            f"| {format_money(draw.cost, draw.lottery.currency)} |"
            for draw in plan.draws
        ]
    else:
        lines.append(t("plan.empty"))

    if plan.is_household:
        lines += [
            "",
            "## " + t("plan.players.title"),
            "",
            "| Player | Budget | Committed | Grids | Unspent |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
        lines += [
            f"| {name} "
            f"| {format_money(plan.budget_of(name), plan.currency)} "
            f"| {format_money(plan.committed_by(name), plan.currency)} "
            f"| {sum(1 for d in plan.draws if d.player == name)} "
            f"| {format_money(plan.budget_of(name) - plan.committed_by(name), plan.currency)} |"
            for name in plan.player_names
        ]

    lines += [
        "",
        "## " + t("plan.summary.title"),
        "",
        f"| {player_column}Lottery | Weight | Allocated | Committed | Grids | Unused |",
        f"| {player_rule}--- | ---: | ---: | ---: | ---: | ---: |",
    ]
    lines += [
        f"| {a.player + ' | ' if plan.is_household else ''}{a.lottery.label} "
        f"| {a.lottery.weight:g} "
        f"| {format_money(a.share, a.lottery.currency)} "
        f"| {format_money(a.committed, a.lottery.currency)} "
        f"| {a.grid_count} "
        f"| {format_money(a.remainder, a.lottery.currency)} |"
        for a in plan.allocations
    ]

    annotations = [
        (f"{a.player} · {a.lottery.label}" if a.player else a.lottery.label, a.note)
        for a in plan.allocations
        if a.note
    ]
    if plan.shared_dates():
        annotations.append(
            (
                "Shared draws",
                f"{len(plan.shared_dates())} draw(s) are played by more than one person. "
                f"Sharing a draw costs nothing in odds.",
            )
        )
    if annotations:
        lines += ["", "### " + t("note.shared"), ""]
        lines += [f"- **{label}**: {note}" for label, note in annotations]

    lines += [
        "",
        "## " + t("plan.totals.title"),
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
