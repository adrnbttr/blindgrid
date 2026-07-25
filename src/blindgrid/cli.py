"""Command line interface.

Three groups of commands: ``generate`` builds a month's plan, ``config``
edits the stable values, ``lottery`` manages game definitions. Everything the
user is asked for at runtime is a decision that changes month to month; the
rest lives in the config file.
"""

from __future__ import annotations

import calendar
from dataclasses import replace
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Annotated, NoReturn

import questionary
import typer
from rich import box
from rich.console import Console
from rich.table import Table
from rich.text import Text

from blindgrid import __version__, config, store
from blindgrid.errors import BlindgridError, BudgetError, ConfigError, StoreError
from blindgrid.export import export_plan
from blindgrid.filters import RULES
from blindgrid.generator import system_rng
from blindgrid.models import WEEKDAY_NAMES, Lottery, Plan, Player, Pool, money
from blindgrid.plan import build_household_plan, build_plan
from blindgrid.render import render_plan

console = Console()
err_console = Console(stderr=True)

app = typer.Typer(
    name="blindgrid",
    help=(
        "Generate lottery grids from cryptographic randomness and plan a month "
        "within a hard budget cap. This tool predicts nothing."
    ),
    no_args_is_help=True,
    add_completion=False,
)
config_app = typer.Typer(help="Inspect and edit the configuration.", no_args_is_help=False)
lottery_app = typer.Typer(help="Manage lottery definitions.", no_args_is_help=True)
player_app = typer.Typer(help="Manage the people who play.", no_args_is_help=True)
app.add_typer(config_app, name="config", invoke_without_command=True)
app.add_typer(lottery_app, name="lottery")
app.add_typer(player_app, name="player")

ConfigOption = Annotated[
    Path | None,
    typer.Option("--config", "-c", help="Path to the configuration file.", show_default=False),
]


def _fatal(message: object) -> NoReturn:
    """Print an error without a traceback and exit non-zero."""
    err_console.print(Text("Error: ", style="bold red") + Text(str(message)))
    raise typer.Exit(code=1)


def _cancelled() -> NoReturn:
    console.print(Text("Cancelled.", style="dim"))
    raise typer.Exit(code=130)


def _answer(question: questionary.Question) -> object:
    """Ask ``question``, treating an interrupted prompt as a cancellation."""
    try:
        result = question.ask()
    except KeyboardInterrupt:
        _cancelled()
    if result is None:
        _cancelled()
    return result


def _load(path: Path | None) -> config.Settings:
    try:
        return config.load(path)
    except ConfigError as exc:
        _fatal(exc)


def _resolve_month(spec: str | None) -> tuple[int, int]:
    """Turn ``YYYY-MM`` into a year/month pair, defaulting to the current month."""
    if spec is None:
        today = date.today()
        return today.year, today.month
    try:
        year_text, month_text = spec.split("-")
        year, month = int(year_text), int(month_text)
        date(year, month, 1)
    except ValueError:
        _fatal(f"{spec!r} is not a valid month. Expected YYYY-MM, for example 2026-08.")
    return year, month


def _parse_budget(raw: str, ceiling: Decimal, who: str | None = None) -> Decimal:
    """Validate a budget against the configured hard ceiling.

    The ceiling has no override, by design. A budget cap that can be raised in
    the moment is not a cap. Each player has their own, and nobody can spend
    against anyone else's.
    """
    owner = f"{who}: " if who else ""
    try:
        amount = money(raw.strip().replace(",", "."))
    except (InvalidOperation, ValueError) as exc:
        raise BudgetError(f"{owner}{raw!r} is not a valid amount") from exc
    if amount <= 0:
        raise BudgetError(f"{owner}budget must be greater than zero.")
    if amount > ceiling:
        raise BudgetError(
            f"{owner}budget of {amount} exceeds the configured ceiling of {ceiling}. "
            f"Raise max_monthly_budget in your config if this is a considered decision."
        )
    return amount


def _select_lotteries(
    settings: config.Settings,
    requested: list[str] | None,
) -> tuple[Lottery, ...]:
    """Resolve the lotteries to play, from options or interactively."""
    available = settings.enabled_lotteries()
    if not available:
        _fatal("No lottery with a non-zero weight is configured.")

    if requested:
        chosen = []
        for label in requested:
            found = settings.find(label)
            if found is None:
                _fatal(
                    f"Unknown lottery {label!r}. Configured: "
                    f"{', '.join(lot.label for lot in settings.lotteries)}"
                )
            chosen.append(found)
        return tuple(chosen)

    picked = _answer(
        questionary.checkbox(
            "Which lotteries do you want to include?",
            choices=[
                questionary.Choice(
                    title=(
                        f"{lot.label} — {lot.price_per_grid} {lot.currency} per grid, "
                        f"weight {lot.weight:g}"
                    ),
                    value=lot.label,
                    checked=True,
                )
                for lot in available
            ],
        )
    )
    if not picked:
        _fatal("No lottery selected.")
    return tuple(lot for lot in available if lot.label in set(picked))


def _collect_budgets(
    settings: config.Settings,
    requested: list[str] | None,
    only: list[str] | None,
) -> dict[str, Decimal]:
    """Work out how much each player is putting in this month.

    ``requested`` holds ``Name=amount`` pairs from the command line. Anyone not
    covered there is asked, and an empty answer means they sit this month out.
    """
    players = settings.players
    if only:
        wanted = {name.casefold() for name in only}
        for name in only:
            if settings.find_player(name) is None:
                _fatal(f"Unknown player {name!r}. Configured: {', '.join(p.name for p in players)}")
        players = tuple(p for p in players if p.name.casefold() in wanted)

    given: dict[str, str] = {}
    for pair in requested or []:
        name, separator, amount = pair.partition("=")
        if not separator:
            _fatal(
                f"With players configured, --budget takes NAME=AMOUNT, for example "
                f"--budget '{players[0].name}=30'. Got {pair!r}."
            )
        player = settings.find_player(name.strip())
        if player is None:
            _fatal(
                f"Unknown player {name.strip()!r}. Configured: "
                f"{', '.join(p.name for p in settings.players)}"
            )
        given[player.name] = amount.strip()

    budgets: dict[str, Decimal] = {}
    for player in players:
        raw = given.get(player.name)
        if raw is None:
            console.print()
            console.print(
                Text(f"{player.name}", style="bold magenta")
                + Text(f" — ceiling {player.max_monthly_budget}, plays ", style="dim")
                + Text(
                    ", ".join(lot.label for lot in settings.lotteries_for(player)) or "nothing",
                    style="dim",
                )
            )
            raw = str(
                _answer(
                    questionary.text(f"Budget for {player.name}? (blank to sit this month out)")
                )
            ).strip()
        if not raw:
            continue
        budgets[player.name] = _parse_budget(raw, player.max_monthly_budget, player.name)

    if not budgets:
        _fatal("Nobody is playing this month.")
    return budgets


def _finish(plan: Plan, settings: config.Settings, export: bool) -> None:
    """Render a plan and, unless asked not to, refresh the Markdown export."""
    render_plan(plan, console)
    if export:
        written = export_plan(plan, settings.export_path)
        console.print(Text(f"Exported to {written}", style="dim"))
        console.print()


@app.command()
def generate(
    config_path: ConfigOption = None,
    budget: Annotated[
        list[str] | None,
        typer.Option(
            "--budget",
            "-b",
            help="Budget to use. With players configured: NAME=AMOUNT, repeatable.",
        ),
    ] = None,
    lottery: Annotated[
        list[str] | None,
        typer.Option("--lottery", "-l", help="Include this lottery. Repeatable. Solo mode only."),
    ] = None,
    player: Annotated[
        list[str] | None,
        typer.Option("--player", "-p", help="Limit the plan to these players. Repeatable."),
    ] = None,
    month: Annotated[
        str | None,
        typer.Option("--month", "-m", help="Month to plan, as YYYY-MM. Defaults to now."),
    ] = None,
    force: Annotated[
        bool,
        typer.Option("--force", help="Draw a new plan even if this month already has one."),
    ] = False,
    export: Annotated[
        bool, typer.Option("--export/--no-export", help="Write the Markdown export.")
    ] = True,
) -> None:
    """Build this month's plan: how much to spend, which draws, which numbers.

    A month is drawn once. Running this again shows the plan you already have,
    so you can come back to it while you fill your grids.
    """
    settings = _load(config_path)
    year, month_number = _resolve_month(month)

    try:
        existing = store.load_for(year, month_number)
    except StoreError as exc:
        # A corrupt file must not block the month. Say so and draw a new plan.
        existing = None
        err_console.print(Text(f"Ignoring the saved plan: {exc}", style="yellow"))

    if existing is not None and not force:
        console.print()
        console.print(
            Text("Plan already drawn on ", style="dim")
            + Text(existing.drawn_on.date().isoformat(), style="bold")
            + Text(". Showing it again — pass --force to draw a new one.", style="dim")
        )
        _finish(existing.plan, settings, export)
        return

    console.print()
    if existing is not None:
        console.print(
            Text("Replacing the plan drawn on ", style="yellow")
            + Text(existing.drawn_on.date().isoformat(), style="bold yellow")
        )
        console.print(
            Text(
                "Redrawing until the numbers look right is the bias this tool removes.",
                style="dim",
            )
        )
        console.print()

    today = date.today()
    not_before = today if (year, month_number) == (today.year, today.month) else None

    try:
        if settings.is_household:
            if lottery:
                _fatal(
                    "--lottery applies to solo mode. With players configured, each "
                    "person's lotteries come from their own weights."
                )
            budgets = _collect_budgets(settings, budget, player)
            plan = build_household_plan(
                budgets=budgets,
                players=settings.players,
                lotteries=settings.lotteries,
                year=year,
                month=month_number,
                rng=system_rng(),
                enabled_filters=settings.enabled_filters,
                not_before=not_before,
            )
        else:
            if player:
                _fatal(
                    "--player needs players in your config. Add one with 'blindgrid player add'."
                )
            console.print(
                Text("Monthly ceiling: ", style="dim")
                + Text(f"{settings.max_monthly_budget}", style="bold")
            )
            raw = budget[0] if budget else str(_answer(questionary.text("Budget for this month?")))
            plan = build_plan(
                budget=_parse_budget(raw, settings.max_monthly_budget),
                lotteries=_select_lotteries(settings, lottery),
                year=year,
                month=month_number,
                rng=system_rng(),
                enabled_filters=settings.enabled_filters,
                not_before=not_before,
            )
    except BlindgridError as exc:
        _fatal(exc)

    try:
        store.save(plan)
    except OSError as exc:
        # The plan is already drawn and valid; failing to file it away is worth
        # a warning, not throwing the month's numbers away.
        err_console.print(
            Text(f"Could not save this plan, it will not be remembered: {exc}", style="yellow")
        )

    _finish(plan, settings, export)


@config_app.callback()
def config_main(ctx: typer.Context, config_path: ConfigOption = None) -> None:
    """Edit the configuration interactively when no subcommand is given."""
    if ctx.invoked_subcommand is None:
        edit(config_path)


@config_app.command("init")
def config_init(
    config_path: ConfigOption = None,
    force: Annotated[
        bool, typer.Option("--force", help="Overwrite an existing configuration.")
    ] = False,
) -> None:
    """Create a configuration file from the shipped example."""
    target = config_path or Path.cwd() / config.CONFIG_FILENAME
    if target.exists() and not force:
        _fatal(f"{target} already exists. Pass --force to overwrite it.")
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(config.example_toml(), encoding="utf-8")
    except (ConfigError, OSError) as exc:
        _fatal(exc)
    console.print(Text(f"Wrote {target}", style="green"))
    console.print(Text("Review the prices and draw days before playing.", style="dim"))


@config_app.command("show")
def config_show(config_path: ConfigOption = None) -> None:
    """Print the active configuration."""
    settings = _load(config_path)
    table = Table(box=box.ROUNDED, show_header=False, padding=(0, 1))
    table.add_column(style="bold")
    # A truncated path is useless: this command exists to tell the user which
    # file is actually in effect.
    table.add_column(overflow="fold")
    table.add_row("File", str(settings.path))
    table.add_row("Monthly ceiling", str(settings.max_monthly_budget))
    table.add_row("Export path", str(settings.export_path))

    plan_path = store.default_path()
    try:
        current = store.load(plan_path)
    except StoreError:
        current = None
        state = "unreadable"
    else:
        state = (
            f"{calendar.month_name[current.plan.month]} {current.plan.year}, "
            f"drawn {current.drawn_on.date().isoformat()}"
            if current
            else "none drawn yet"
        )
    table.add_row("Current plan", f"{plan_path}\n{state}")
    table.add_row(
        "Filters",
        ", ".join(sorted(settings.enabled_filters)) or "none",
    )
    table.add_row("Lotteries", str(len(settings.lotteries)))
    console.print()
    console.print(table)
    console.print()


@config_app.command("edit")
def edit(config_path: ConfigOption = None) -> None:
    """Walk through the configuration values one by one."""
    settings = _load(config_path)

    ceiling = str(
        _answer(questionary.text("Hard monthly ceiling?", default=str(settings.max_monthly_budget)))
    )
    export_path = str(
        _answer(questionary.text("Export the plan to?", default=str(settings.export_path)))
    )
    enabled = _answer(
        questionary.checkbox(
            "Active anti-pattern filters",
            choices=[
                questionary.Choice(
                    title=f"{rule.name} — {rule.description}",
                    value=rule.name,
                    checked=rule.name in settings.enabled_filters,
                )
                for rule in RULES
            ],
        )
    )

    try:
        amount = money(ceiling.strip().replace(",", "."))
    except (InvalidOperation, ValueError):
        _fatal(f"{ceiling!r} is not a valid amount")

    updated = replace(
        settings,
        max_monthly_budget=amount,
        export_path=Path(export_path).expanduser(),
        enabled_filters=frozenset(enabled),  # type: ignore[arg-type]
    )
    written = config.save(updated, config_path)
    console.print(Text(f"Saved {written}", style="green"))


@lottery_app.command("list")
def lottery_list(config_path: ConfigOption = None) -> None:
    """Show every configured lottery."""
    settings = _load(config_path)
    table = Table(box=box.ROUNDED, header_style="bold", padding=(0, 1))
    table.add_column("Lottery", style="bold")
    table.add_column("Price", justify="right")
    table.add_column("Draw days")
    table.add_column("Weight", justify="right")
    table.add_column("Pools")

    for lot in settings.lotteries:
        table.add_row(
            lot.label,
            f"{lot.price_per_grid} {lot.currency}",
            ", ".join(WEEKDAY_NAMES[day].capitalize() for day in sorted(lot.draw_days)),
            f"{lot.weight:g}",
            " · ".join(f"{pool.name} {pool.count}/{pool.maximum}" for pool in lot.pools),
            style="dim" if not lot.is_enabled else "",
        )
    console.print()
    console.print(table)
    console.print()


def _ask_pools() -> tuple[Pool, ...]:
    pools: list[Pool] = []
    while True:
        name = str(_answer(questionary.text(f"Pool {len(pools) + 1} name?", default="numbers")))
        count = str(_answer(questionary.text("How many numbers are drawn?")))
        maximum = str(_answer(questionary.text("Drawn from 1 to?")))
        try:
            pools.append(Pool(name=name, count=int(count), maximum=int(maximum)))
        except ValueError as exc:
            _fatal(exc)
        if not _answer(questionary.confirm("Add another pool?", default=False)):
            return tuple(pools)


@lottery_app.command("add")
def lottery_add(config_path: ConfigOption = None) -> None:
    """Add a lottery definition, or replace one with the same label."""
    settings = _load(config_path)

    label = str(_answer(questionary.text("Label?")))
    currency = str(_answer(questionary.text("Currency?", default="EUR")))
    price = str(_answer(questionary.text("Price per grid?")))
    days = _answer(
        questionary.checkbox(
            "Draw days",
            choices=[questionary.Choice(name.capitalize(), value=name) for name in WEEKDAY_NAMES],
        )
    )
    weight = str(_answer(questionary.text("Weight? (relative share, 0 disables)", default="1.0")))
    pools = _ask_pools()

    try:
        lottery = Lottery(
            label=label,
            currency=currency,
            price_per_grid=money(price.strip().replace(",", ".")),
            draw_days=frozenset(WEEKDAY_NAMES.index(day) for day in days),  # type: ignore[union-attr]
            weight=float(weight),
            pools=pools,
        )
    except (InvalidOperation, TypeError, ValueError) as exc:
        _fatal(exc)

    written = config.save(config.with_lottery(settings, lottery), config_path)
    console.print(Text(f"Saved {lottery.label} to {written}", style="green"))


def _ask_weights(settings: config.Settings, existing: Player | None) -> dict[str, float]:
    """Ask which lotteries someone plays, then how they split their budget."""
    if not settings.lotteries:
        _fatal("Add a lottery first with 'blindgrid lottery add'.")

    chosen = _answer(
        questionary.checkbox(
            "Which lotteries does this person play?",
            choices=[
                questionary.Choice(
                    title=f"{lot.label} — {lot.price_per_grid} {lot.currency} per grid",
                    value=lot.label,
                    checked=existing.plays(lot) if existing else True,
                )
                for lot in settings.lotteries
            ],
        )
    )
    if not chosen:
        _fatal("Someone who plays nothing has nothing to plan.")

    console.print()
    console.print(
        Text("Weights are relative shares of that person's budget, not draw counts. ", style="dim")
    )
    console.print(
        Text("Equal weights split it evenly; 0.5 means half as much as a 1.0.", style="dim")
    )

    weights: dict[str, float] = {}
    for label in chosen:  # type: ignore[union-attr]
        default = existing.weights.get(label, 1.0) if existing else 1.0
        raw = str(_answer(questionary.text(f"Weight for {label}?", default=f"{default:g}"))).strip()
        try:
            value = float(raw.replace(",", "."))
        except ValueError:
            _fatal(f"{raw!r} is not a number")
        if value <= 0:
            _fatal(f"Weight for {label} must be greater than zero, or leave it unchecked.")
        weights[label] = value
    return weights


@player_app.command("add")
def player_add(config_path: ConfigOption = None) -> None:
    """Add someone who plays, or update them if the name already exists.

    Everyone keeps their own ceiling and their own lotteries. Configuring a
    second person switches `generate` to household mode, where draws are spread
    across dates so the same game is not played twice on the same day.
    """
    settings = _load(config_path)

    name = str(_answer(questionary.text("Name?"))).strip()
    if not name:
        _fatal("A player needs a name.")

    existing = settings.find_player(name)
    if existing is not None:
        console.print(Text(f"Updating {existing.name}.", style="dim"))

    ceiling = str(
        _answer(
            questionary.text(
                f"Hard monthly ceiling for {name}?",
                default=str(existing.max_monthly_budget)
                if existing
                else str(settings.max_monthly_budget),
            )
        )
    )
    weights = _ask_weights(settings, existing)

    try:
        player = Player(
            name=name,
            max_monthly_budget=money(ceiling.strip().replace(",", ".")),
            weights=weights,
        )
    except (InvalidOperation, TypeError, ValueError) as exc:
        _fatal(exc)

    written = config.save(config.with_player(settings, player), config_path)
    console.print(Text(f"Saved {player.name} to {written}", style="green"))
    if len(settings.players) == 0:
        console.print(
            Text("Add a second person and 'generate' will plan for the household.", style="dim")
        )


@player_app.command("list")
def player_list(config_path: ConfigOption = None) -> None:
    """Show everyone who plays, with their ceiling and preferences."""
    settings = _load(config_path)
    if not settings.players:
        console.print()
        console.print(Text("No players configured — 'generate' plans for one person.", style="dim"))
        console.print(Text("Add someone with 'blindgrid player add'.", style="dim"))
        console.print()
        return

    table = Table(box=box.ROUNDED, header_style="bold", padding=(0, 1))
    table.add_column("Player", style="bold magenta")
    table.add_column("Ceiling", justify="right")
    table.add_column("Plays")

    for person in settings.players:
        table.add_row(
            person.name,
            str(person.max_monthly_budget),
            ", ".join(
                f"{lot.label} ({person.weight_for(lot):g})"
                for lot in settings.lotteries_for(person)
            )
            or "nothing",
        )
    console.print()
    console.print(table)
    console.print()


@player_app.command("remove")
def player_remove(
    name: Annotated[str, typer.Argument(help="Who to remove.")],
    config_path: ConfigOption = None,
) -> None:
    """Remove someone. Their configuration is deleted, nothing else."""
    settings = _load(config_path)
    if settings.find_player(name) is None:
        _fatal(
            f"Unknown player {name!r}. Configured: "
            f"{', '.join(p.name for p in settings.players) or 'none'}"
        )
    written = config.save(config.without_player(settings, name), config_path)
    console.print(Text(f"Removed {name} from {written}", style="green"))


@app.command()
def version() -> None:
    """Print the installed version."""
    console.print(f"blindgrid {__version__}")


if __name__ == "__main__":
    app()
