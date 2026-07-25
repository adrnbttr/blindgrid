"""Terminal rendering of a plan.

The summary table is not decoration. Showing the theoretical allocation next
to what was actually committed is what makes the weighting legible, and what
makes an unspent remainder read as a deliberate outcome rather than a bug.
"""

from __future__ import annotations

import calendar
from decimal import Decimal

from rich import box
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from blindgrid.models import Grid, Plan, Pool

DISCLAIMER = (
    "Draws are independent events. These numbers are not predictions, "
    "and no combination is more likely than another."
)


def format_money(amount: Decimal, currency: str) -> str:
    return f"{amount:.2f} {currency}"


def format_numbers(grids: tuple[Grid, ...], pools: tuple[Pool, ...]) -> Text:
    """Render a grid as ``7 19 34 41 48 · stars 3 9``.

    Numbers are zero-padded to the width of the pool maximum so columns line
    up vertically across rows, which is what makes a long plan scannable.
    """
    widths = {pool.name: len(str(pool.maximum)) for pool in pools}
    text = Text()
    for index, grid in enumerate(grids):
        if index:
            text.append("  ·  ", style="dim")
            text.append(f"{grid.pool_name} ", style="dim italic")
        width = widths.get(grid.pool_name, 2)
        text.append(
            " ".join(str(number).rjust(width) for number in grid.numbers),
            style="bold" if index == 0 else "cyan",
        )
    return text


def draws_table(plan: Plan) -> Table:
    table = Table(
        title=f"Draws to play — {calendar.month_name[plan.month]} {plan.year}",
        box=box.ROUNDED,
        header_style="bold",
        title_style="bold",
        padding=(0, 1),
        expand=False,
    )
    table.add_column("Date", style="dim", no_wrap=True)
    table.add_column("Day", no_wrap=True)
    table.add_column("Lottery", style="bold")
    table.add_column("Numbers")
    table.add_column("Cost", justify="right", no_wrap=True)

    for draw in plan.draws:
        table.add_row(
            draw.draw_date.isoformat(),
            draw.weekday_name,
            draw.lottery.label,
            format_numbers(draw.grids, draw.lottery.pools),
            format_money(draw.cost, draw.lottery.currency),
        )
    return table


def summary_table(plan: Plan) -> Table:
    table = Table(
        title="Budget allocation",
        box=box.ROUNDED,
        header_style="bold",
        title_style="bold",
        padding=(0, 1),
        expand=False,
    )
    table.add_column("Lottery", style="bold")
    table.add_column("Weight", justify="right")
    table.add_column("Allocated", justify="right")
    table.add_column("Committed", justify="right")
    table.add_column("Grids", justify="right")
    table.add_column("Unused", justify="right", style="dim")

    for allocation in plan.allocations:
        currency = allocation.lottery.currency
        style = "dim" if allocation.is_skipped else ""
        table.add_row(
            allocation.lottery.label,
            f"{allocation.lottery.weight:g}",
            format_money(allocation.share, currency),
            format_money(allocation.committed, currency),
            str(allocation.grid_count),
            format_money(allocation.remainder, currency),
            style=style,
        )
    return table


def notes(plan: Plan) -> Text | None:
    """Structural reasons why a lottery got less than its share."""
    lines = [
        (allocation.lottery.label, allocation.note)
        for allocation in plan.allocations
        if allocation.note
    ]
    if not lines:
        return None

    text = Text()
    for index, (label, note) in enumerate(lines):
        if index:
            text.append("\n")
        text.append("  · ", style="yellow")
        text.append(f"{label}: ", style="bold")
        text.append(note, style="dim")
    return text


def totals_panel(plan: Plan) -> Panel:
    """The bottom line: what was budgeted, what is committed, what stays unspent."""
    currency = plan.currency
    body = Text()
    body.append("Budget      ", style="dim")
    body.append(format_money(plan.budget, currency), style="bold")
    body.append("\nCommitted   ", style="dim")
    body.append(format_money(plan.total_committed, currency), style="bold green")
    body.append("\nUnspent     ", style="dim")
    body.append(format_money(plan.unspent, currency), style="bold")
    return Panel(body, box=box.ROUNDED, expand=False, padding=(1, 3), title="Totals")


def render_plan(plan: Plan, console: Console) -> None:
    """Print the full plan: draws, allocation summary, notes and totals."""
    console.print()
    if plan.draws:
        console.print(draws_table(plan))
        console.print()
    else:
        console.print(Text("No draw could be planned with this budget.", style="bold yellow"), "\n")

    console.print(Group(summary_table(plan)))
    annotations = notes(plan)
    if annotations is not None:
        console.print()
        console.print(annotations)
    console.print()
    console.print(totals_panel(plan))
    console.print(Text(DISCLAIMER, style="dim italic"), width=76)
    console.print()
