"""Terminal rendering of a plan.

The summary table is not decoration. Showing the theoretical allocation next
to what was actually committed is what makes the weighting legible, and what
makes an unspent remainder read as a deliberate outcome rather than a bug.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from rich import box
from rich.console import Console, Group
from rich.measure import Measurement
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from blindgrid.i18n import month_name, t, weekday_name
from blindgrid.models import Grid, Plan, Pool

# How many shared draws to name before trailing off.
SHARED_SHOWN = 3


def format_money(amount: Decimal, currency: str) -> str:
    return f"{amount:.2f} {currency}"


@dataclass(frozen=True, slots=True)
class NumberLayout:
    """Column widths shared by every row of a plan.

    A plan mixes lotteries of different shapes — five numbers here, six there,
    one bonus ball or two. Sizing each row on its own would leave the
    separators and pool names drifting left and right down the table, which is
    exactly the kind of visual noise that makes a list of numbers hard to
    check against a ticket. These widths are measured across the whole plan so
    every row lines up.
    """

    blocks: tuple[int, ...]
    labels: tuple[int, ...]

    @classmethod
    def measure(cls, plan: Plan) -> NumberLayout:
        blocks: dict[int, int] = {}
        labels: dict[int, int] = {}
        for draw in plan.draws:
            for position, (grid, pool) in enumerate(
                zip(draw.grids, draw.lottery.pools, strict=False)
            ):
                digits = len(str(pool.maximum))
                width = len(grid.numbers) * digits + max(len(grid.numbers) - 1, 0)
                blocks[position] = max(blocks.get(position, 0), width)
                labels[position] = max(labels.get(position, 0), len(grid.pool_name))

        return cls(
            blocks=tuple(blocks.get(i, 0) for i in range(len(blocks))),
            labels=tuple(labels.get(i, 0) for i in range(len(labels))),
        )

    def block(self, position: int) -> int:
        return self.blocks[position] if position < len(self.blocks) else 0

    def label(self, position: int) -> int:
        return self.labels[position] if position < len(self.labels) else 0


def format_numbers(
    grids: tuple[Grid, ...],
    pools: tuple[Pool, ...],
    layout: NumberLayout | None = None,
) -> Text:
    """Render a grid as ``7 19 34 41 48 · stars 3 9``.

    Numbers are right-aligned to the width of their pool maximum, and each
    block is padded to the widest one in the plan, so separators and pool
    names sit in the same column on every row.
    """
    digits = {pool.name: len(str(pool.maximum)) for pool in pools}
    text = Text()

    for position, grid in enumerate(grids):
        if position:
            text.append("  ·  ", style="dim")
            text.append(
                grid.pool_name.ljust(layout.label(position) if layout else 0) + " ",
                style="dim italic",
            )

        width = digits.get(grid.pool_name, 2)
        rendered = " ".join(str(number).rjust(width) for number in grid.numbers)
        if layout:
            rendered = rendered.ljust(layout.block(position))
        text.append(rendered, style="bold" if position == 0 else "cyan")

    return text


def draws_table(plan: Plan) -> Table:
    table = Table(
        title=t("plan.title", month=month_name(plan.month), year=plan.year),
        box=box.ROUNDED,
        header_style="bold",
        title_style="bold",
        padding=(0, 1),
        expand=False,
    )
    table.add_column(t("plan.column.date"), style="dim", no_wrap=True)
    table.add_column(t("plan.column.day"), no_wrap=True)
    if plan.is_household:
        table.add_column(t("plan.column.player"), style="magenta", no_wrap=True)
    table.add_column(t("plan.column.lottery"), style="bold")
    table.add_column(t("plan.column.numbers"))
    table.add_column(t("plan.column.cost"), justify="right", no_wrap=True)

    today = date.today()
    layout = NumberLayout.measure(plan)
    for draw in plan.draws:
        cells = [draw.draw_date.isoformat(), weekday_name(draw.draw_date.weekday())]
        if plan.is_household:
            cells.append(draw.player or "")
        cells += [
            draw.lottery.label,
            format_numbers(draw.grids, draw.lottery.pools, layout),
            format_money(draw.cost, draw.lottery.currency),
        ]
        # A plan reopened mid-month still lists the draws it opened with. Dim
        # the ones that have already happened so what is left to play stands out.
        table.add_row(*cells, style="dim strike" if draw.draw_date < today else "")
    return table


def players_table(plan: Plan) -> Table:
    """Per-player totals, so each person can see their own month."""
    table = Table(
        title=t("plan.players.title"),
        box=box.ROUNDED,
        header_style="bold",
        title_style="bold",
        padding=(0, 1),
        expand=False,
    )
    table.add_column(t("plan.column.player"), style="bold magenta")
    table.add_column(t("plan.column.budget"), justify="right")
    table.add_column(t("plan.column.committed"), justify="right")
    table.add_column(t("plan.column.grids"), justify="right")
    table.add_column(t("plan.column.unspent"), justify="right", style="dim")
    table.add_column(t("plan.column.plays"))

    currency = plan.currency
    for name in plan.player_names:
        budget = plan.budget_of(name)
        committed = plan.committed_by(name)
        labels = [
            a.lottery.label for a in plan.allocations if a.player == name and not a.is_skipped
        ]
        table.add_row(
            name,
            format_money(budget, currency),
            format_money(committed, currency),
            str(sum(1 for d in plan.draws if d.player == name)),
            format_money(budget - committed, currency),
            ", ".join(labels) or t("plan.plays.nothing"),
        )
    return table


def format_weights(plan: Plan) -> dict[float, str]:
    """Render every weight in a plan to the same number of decimals.

    Mixing ``1`` and ``0.4`` in a right-aligned column puts the decimal points
    on different characters. One shared precision, chosen from the values
    actually present, keeps them in a line without adding noise to a table of
    whole numbers.
    """
    weights = {allocation.lottery.weight for allocation in plan.allocations}
    decimals = 0
    for weight in weights:
        text = f"{weight:g}"
        if "." in text:
            decimals = max(decimals, len(text.split(".")[1]))
    return {weight: f"{weight:.{decimals}f}" for weight in weights}


def summary_table(plan: Plan) -> Table:
    table = Table(
        title=t("plan.summary.title"),
        box=box.ROUNDED,
        header_style="bold",
        title_style="bold",
        padding=(0, 1),
        expand=False,
    )
    if plan.is_household:
        table.add_column(t("plan.column.player"), style="magenta", no_wrap=True)
    table.add_column(t("plan.column.lottery"), style="bold")
    table.add_column(t("plan.column.weight"), justify="right")
    table.add_column(t("plan.column.allocated"), justify="right")
    table.add_column(t("plan.column.committed"), justify="right")
    table.add_column(t("plan.column.grids"), justify="right")
    table.add_column(t("plan.column.unused"), justify="right", style="dim")

    weights = format_weights(plan)
    for allocation in plan.allocations:
        currency = allocation.lottery.currency
        cells = [allocation.player or ""] if plan.is_household else []
        cells += [
            allocation.lottery.label,
            weights[allocation.lottery.weight],
            format_money(allocation.share, currency),
            format_money(allocation.committed, currency),
            str(allocation.grid_count),
            format_money(allocation.remainder, currency),
        ]
        table.add_row(*cells, style="dim" if allocation.is_skipped else "")
    return table


def notes(plan: Plan) -> Text | None:
    """Structural reasons why a lottery got less than its share."""
    lines = [
        (
            f"{a.player} · {a.lottery.label}" if a.player else a.lottery.label,
            a.note,
        )
        for a in plan.allocations
        if a.note
    ]

    shared = plan.shared_dates()
    if shared:
        listed = ", ".join(f"{label} on {day.isoformat()}" for day, label in shared[:SHARED_SHOWN])
        lines.append(
            (
                t("note.shared"),
                t(
                    "note.shared.body",
                    count=len(shared),
                    listed=listed + (", …" if len(shared) > SHARED_SHOWN else ""),
                ),
            )
        )

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
    body.append(t("plan.column.budget").ljust(11) + " ", style="dim")
    body.append(format_money(plan.budget, currency), style="bold")
    body.append("\n" + t("plan.column.committed").ljust(11) + " ", style="dim")
    body.append(format_money(plan.total_committed, currency), style="bold green")
    body.append("\n" + t("plan.column.unspent").ljust(11) + " ", style="dim")
    body.append(format_money(plan.unspent, currency), style="bold")
    return Panel(
        body,
        box=box.ROUNDED,
        expand=False,
        padding=(1, 3),
        title=t("plan.totals.household") if plan.is_household else t("plan.totals.title"),
    )


def compact_draws(plan: Plan) -> Text:
    """The plan as a list, for terminals too narrow for the table.

    Two lines per draw. The numbers get a line of their own and are never
    allowed to wrap: they are the one thing being copied onto a paper slip,
    and a table squeezed into 60 columns turns them into a vertical stack of
    single digits with the lottery name cut to "Eur…".

    Readable from about 40 columns, which covers a phone and an iPad in
    portrait.
    """
    text = Text()
    today = date.today()

    for index, draw in enumerate(plan.draws):
        if index:
            text.append("\n")

        past = draw.draw_date < today
        heading = Text()
        heading.append(f"{draw.draw_date.day:2d} ", style="bold")
        heading.append(f"{weekday_name(draw.draw_date.weekday())[:3]}  ", style="dim")
        heading.append(draw.lottery.label, style="bold")
        if draw.player:
            heading.append(f"  {draw.player}", style="magenta")
        heading.append(f"  {format_money(draw.cost, draw.lottery.currency)}", style="dim")
        if past:
            heading.stylize("dim strike")
        text.append(heading)

        text.append("\n    ")
        numbers = format_numbers(draw.grids, draw.lottery.pools)
        if past:
            numbers.stylize("dim strike")
        text.append(numbers)
        text.append("\n")

    return text


def compact_summary(plan: Plan) -> Text:
    """Per-player and total figures as plain lines rather than tables."""
    currency = plan.currency
    text = Text()

    for name in plan.player_names:
        budget = plan.budget_of(name)
        committed = plan.committed_by(name)
        text.append(f"{name}  ", style="bold magenta")
        text.append(
            f"{format_money(committed, currency)} / {format_money(budget, currency)}\n",
            style="dim",
        )

    if plan.player_names:
        text.append("\n")

    for key, value, style in (
        ("plan.column.budget", plan.budget, "bold"),
        ("plan.column.committed", plan.total_committed, "bold green"),
        ("plan.column.unspent", plan.unspent, "bold"),
    ):
        text.append(f"{t(key):<12}", style="dim")
        text.append(f"{format_money(value, currency)}\n", style=style)

    return text


def fits(renderable: Table, console: Console) -> bool:
    """Whether ``renderable`` can be drawn without squeezing its columns.

    Measured against an effectively unbounded width: asking for a measurement
    with the console's own options caps the answer at the console width, which
    would make everything look like it fits.
    """
    unbounded = console.options.update(max_width=10_000)
    return Measurement.get(console, unbounded, renderable).maximum <= console.width


def render_plan(plan: Plan, console: Console, compact: bool | None = None) -> None:
    """Print the full plan: draws, allocation summary, notes and totals.

    ``compact`` forces the narrow layout on or off; left as ``None`` it is
    chosen by measuring whether the table actually fits.
    """
    console.print()

    if not plan.draws:
        console.print(Text(t("plan.empty"), style="bold yellow"), "\n")
    else:
        table = draws_table(plan)
        narrow = compact if compact is not None else not fits(table, console)
        if narrow:
            console.print(Text(f"{month_name(plan.month)} {plan.year}", style="bold"))
            console.print()
            console.print(compact_draws(plan))
            console.print(compact_summary(plan))
            _print_notes(plan, console)
            console.print(Text(t("plan.disclaimer"), style="dim italic"))
            console.print()
            return

        console.print(table)
        console.print()

    if plan.is_household:
        console.print(players_table(plan))
        console.print()

    console.print(Group(summary_table(plan)))
    _print_notes(plan, console)
    console.print()
    console.print(totals_panel(plan))
    console.print(Text(t("plan.disclaimer"), style="dim italic"), width=76)


def _print_notes(plan: Plan, console: Console) -> None:
    annotations = notes(plan)
    if annotations is not None:
        console.print()
        console.print(annotations)
    console.print()
