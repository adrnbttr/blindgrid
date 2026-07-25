"""Command line interface.

Three groups of commands: ``generate`` builds a month's plan, ``config``
edits the stable values, ``lottery`` manages game definitions. Everything the
user is asked for at runtime is a decision that changes month to month; the
rest lives in the config file.
"""

from __future__ import annotations

import re
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

from blindgrid import __version__, config, i18n, store
from blindgrid.errors import BlindgridError, BudgetError, ConfigError, StoreError
from blindgrid.export import export_plan
from blindgrid.filters import RULES
from blindgrid.generator import system_rng
from blindgrid.i18n import t
from blindgrid.models import WEEKDAY_NAMES, Lottery, Plan, Player, Pool, money
from blindgrid.plan import build_household_plan, build_plan
from blindgrid.render import render_plan

console = Console()
err_console = Console(stderr=True)

# Typer builds its help text when this module is imported, before any command
# runs, so the language has to be settled here. --lang and the config file are
# applied later, once they are known.
i18n.activate(i18n.resolve())

app = typer.Typer(
    name="blindgrid",
    help=t("app.help"),
    no_args_is_help=True,
    add_completion=False,
)
config_app = typer.Typer(help=t("config.help"), no_args_is_help=False)
lottery_app = typer.Typer(help=t("lottery.help"), no_args_is_help=True)
player_app = typer.Typer(help=t("player.help"), no_args_is_help=True)
app.add_typer(config_app, name="config", invoke_without_command=True)
app.add_typer(lottery_app, name="lottery")
app.add_typer(player_app, name="player")


_requested_language: str | None = None


@app.callback()
def main(lang: LangOption = None) -> None:
    """Accept --lang before the command as well as after it."""
    global _requested_language  # noqa: PLW0603 - one setting for the whole run
    # Assigned unconditionally: the process normally runs one command, but the
    # test runner reuses it, and a stale value would leak into the next call.
    _requested_language = lang
    if lang:
        _apply_language(lang)


ConfigOption = Annotated[
    Path | None,
    typer.Option("--config", "-c", help=t("option.config"), show_default=False),
]
LangOption = Annotated[
    str | None,
    typer.Option("--lang", help=t("option.lang"), show_default=False),
]


def _apply_language(explicit: str | None, settings: config.Settings | None = None) -> None:
    """Settle the language for this run, once the options and config are known."""
    explicit = explicit or _requested_language
    if explicit and i18n.normalise(explicit) is None:
        _fatal(t("error.language", value=repr(explicit), known=", ".join(i18n.available())))
    i18n.activate(i18n.resolve(explicit, settings.language if settings else None))


def _fatal(message: object) -> NoReturn:
    """Print an error without a traceback and exit non-zero."""
    err_console.print(Text(t("error.prefix"), style="bold red") + Text(str(message)))
    raise typer.Exit(code=1)


def _cancelled() -> NoReturn:
    console.print(Text(t("error.cancelled"), style="dim"))
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
        _fatal(t("error.month", value=repr(spec)))
    return year, month


# Typing "30 €" or "30 EUR" is the natural reflex, and the currency is already
# known from the configuration. Thin spaces come from keyboards and from paste.
ISO_CODE = re.compile(r"(?<=[\d\s])[A-Za-z]{3}$")
CURRENCY_NOISE = re.compile(r"[€$£¥\s\u00a0\u202f]")


def _clean_amount(raw: str) -> str:
    """Strip currency decoration so a typed amount parses as a number."""
    without_code = ISO_CODE.sub("", raw.strip())
    return CURRENCY_NOISE.sub("", without_code).replace(",", ".")


def _parse_budget(raw: str, ceiling: Decimal, who: str | None = None) -> Decimal:
    """Validate a budget against the configured hard ceiling.

    The ceiling has no override, by design. A budget cap that can be raised in
    the moment is not a cap. Each player has their own, and nobody can spend
    against anyone else's.
    """
    owner = f"{who}: " if who else ""
    try:
        amount = money(_clean_amount(raw))
    except (InvalidOperation, ValueError) as exc:
        raise BudgetError(t("error.budget.invalid", who=owner, value=repr(raw))) from exc
    if amount <= 0:
        raise BudgetError(t("error.budget.zero", who=owner))
    if amount > ceiling:
        raise BudgetError(t("error.budget.ceiling", who=owner, amount=amount, ceiling=ceiling))
    return amount


def _select_lotteries(
    settings: config.Settings,
    requested: list[str] | None,
) -> tuple[Lottery, ...]:
    """Resolve the lotteries to play, from options or interactively."""
    available = settings.enabled_lotteries()
    if not available:
        _fatal(t("error.no.lottery"))

    if requested:
        chosen = []
        for label in requested:
            found = settings.find(label)
            if found is None:
                _fatal(
                    t(
                        "error.lottery.unknown",
                        label=repr(label),
                        known=", ".join(lot.label for lot in settings.lotteries),
                    )
                )
            chosen.append(found)
        return tuple(chosen)

    picked = _answer(
        questionary.checkbox(
            t("prompt.lotteries"),
            choices=[
                questionary.Choice(
                    title=f"{lot.label} — "
                    + t(
                        "choice.per.grid.weight",
                        price=lot.price_per_grid,
                        currency=lot.currency,
                        weight=f"{lot.weight:g}",
                    ),
                    value=lot.label,
                    checked=True,
                )
                for lot in available
            ],
        )
    )
    if not picked:
        _fatal(t("error.none.selected"))
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
                _fatal(
                    t(
                        "error.player.unknown",
                        name=repr(name),
                        known=", ".join(p.name for p in players),
                    )
                )
        players = tuple(p for p in players if p.name.casefold() in wanted)

    given: dict[str, str] = {}
    for pair in requested or []:
        name, separator, amount = pair.partition("=")
        if not separator:
            _fatal(t("error.budget.format", example=players[0].name, value=repr(pair)))
        player = settings.find_player(name.strip())
        if player is None:
            _fatal(
                t(
                    "error.player.unknown",
                    name=repr(name.strip()),
                    known=", ".join(p.name for p in settings.players),
                )
            )
        given[player.name] = amount.strip()

    budgets: dict[str, Decimal] = {}
    for player in players:
        raw = given.get(player.name)
        if raw is None:
            console.print()
            console.print(
                Text(
                    t(
                        "plan.player.line",
                        name=player.name,
                        ceiling=player.max_monthly_budget,
                        lotteries=", ".join(lot.label for lot in settings.lotteries_for(player))
                        or t("plan.player.nothing"),
                    ),
                    style="dim",
                )
            )
            raw = str(
                _answer(questionary.text(t("prompt.budget.player", name=player.name)))
            ).strip()
        if not raw:
            continue
        budgets[player.name] = _parse_budget(raw, player.max_monthly_budget, player.name)

    if not budgets:
        _fatal(t("error.nobody"))
    return budgets


def _finish(plan: Plan, settings: config.Settings, export: bool) -> None:
    """Render a plan and, unless asked not to, refresh the Markdown export."""
    render_plan(plan, console)
    if export:
        written = export_plan(plan, settings.export_path)
        console.print(Text(t("plan.exported", path=written), style="dim"))
        console.print()


@app.command(help=t("generate.help"))
def generate(
    config_path: ConfigOption = None,
    lang: LangOption = None,
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
        typer.Option("--player", "-p", help=t("option.player")),
    ] = None,
    month: Annotated[
        str | None,
        typer.Option("--month", "-m", help=t("option.month")),
    ] = None,
    force: Annotated[
        bool,
        typer.Option("--force", help=t("option.force")),
    ] = False,
    export: Annotated[bool, typer.Option("--export/--no-export", help=t("option.export"))] = True,
) -> None:
    """Build this month's plan: how much to spend, which draws, which numbers.

    A month is drawn once. Running this again shows the plan you already have,
    so you can come back to it while you fill your grids.
    """
    settings = _load(config_path)
    _apply_language(lang, settings)
    year, month_number = _resolve_month(month)

    try:
        existing = store.load_for(year, month_number)
    except StoreError as exc:
        # A corrupt file must not block the month. Say so and draw a new plan.
        existing = None
        err_console.print(Text(t("error.plan.ignored", reason=exc), style="yellow"))

    if existing is not None and not force:
        console.print()
        console.print(
            Text(
                t("plan.already.drawn", date=existing.drawn_on.date().isoformat()),
                style="dim",
            )
        )
        _finish(existing.plan, settings, export)
        return

    console.print()
    if existing is not None:
        console.print(
            Text(
                t("plan.replacing", date=existing.drawn_on.date().isoformat()),
                style="yellow",
            )
        )
        console.print(Text(t("plan.replacing.warning"), style="dim"))
        console.print()

    today = date.today()
    not_before = today if (year, month_number) == (today.year, today.month) else None

    try:
        if settings.is_household:
            if lottery:
                _fatal(t("error.lottery.solo"))
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
                _fatal(t("error.player.solo"))
            console.print(
                Text(t("plan.ceiling"), style="dim")
                + Text(f"{settings.max_monthly_budget}", style="bold")
            )
            raw = budget[0] if budget else str(_answer(questionary.text(t("prompt.budget"))))
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
        err_console.print(Text(t("error.plan.unsaved", reason=exc), style="yellow"))

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
        _fatal(t("error.exists", path=target))
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(config.example_toml(), encoding="utf-8")
    except (ConfigError, OSError) as exc:
        _fatal(exc)
    console.print(Text(t("config.wrote", path=target), style="green"))
    console.print(Text(t("config.review"), style="dim"))


@config_app.command("show")
def config_show(config_path: ConfigOption = None, lang: LangOption = None) -> None:
    """Print the active configuration."""
    settings = _load(config_path)
    _apply_language(lang, settings)
    table = Table(box=box.ROUNDED, show_header=False, padding=(0, 1))
    table.add_column(style="bold")
    # A truncated path is useless: this command exists to tell the user which
    # file is actually in effect.
    table.add_column(overflow="fold")
    table.add_row(t("config.file"), str(settings.path))
    table.add_row(t("config.ceiling"), str(settings.max_monthly_budget))
    table.add_row(t("config.export"), str(settings.export_path))

    plan_path = store.default_path()
    try:
        current = store.load(plan_path)
    except StoreError:
        current = None
        state = t("config.plan.unreadable")
    else:
        state = (
            t(
                "config.plan.drawn",
                month=i18n.month_name(current.plan.month),
                year=current.plan.year,
                date=current.drawn_on.date().isoformat(),
            )
            if current
            else t("config.plan.none")
        )
    table.add_row(t("config.plan"), f"{plan_path}\n{state}")
    table.add_row(
        t("config.filters"),
        ", ".join(sorted(settings.enabled_filters)) or t("config.none"),
    )
    table.add_row(t("config.lotteries"), str(len(settings.lotteries)))
    console.print()
    console.print(table)
    console.print()


@config_app.command("edit")
def edit(config_path: ConfigOption = None, lang: LangOption = None) -> None:
    """Walk through the configuration values one by one."""
    settings = _load(config_path)
    _apply_language(lang, settings)

    chosen_language = _answer(
        questionary.select(
            t("prompt.language"),
            choices=[
                questionary.Choice(title=i18n.LANGUAGE_NAMES[code], value=code)
                for code in i18n.available()
            ],
            default=settings.language or i18n.current(),
        )
    )
    i18n.activate(str(chosen_language))

    ceiling = str(
        _answer(questionary.text(t("prompt.ceiling"), default=str(settings.max_monthly_budget)))
    )
    export_path = str(
        _answer(questionary.text(t("prompt.export"), default=str(settings.export_path)))
    )
    enabled = _answer(
        questionary.checkbox(
            t("prompt.filters"),
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
        amount = money(_clean_amount(ceiling))
    except (InvalidOperation, ValueError):
        _fatal(t("error.budget.invalid", who="", value=repr(ceiling)))

    updated = replace(
        settings,
        max_monthly_budget=amount,
        language=str(chosen_language),
        export_path=Path(export_path).expanduser(),
        enabled_filters=frozenset(enabled),  # type: ignore[arg-type]
    )
    written = config.save(updated, config_path)
    console.print(Text(t("config.saved", path=written), style="green"))


@lottery_app.command("list")
def lottery_list(config_path: ConfigOption = None, lang: LangOption = None) -> None:
    """Show every configured lottery."""
    settings = _load(config_path)
    _apply_language(lang, settings)
    table = Table(box=box.ROUNDED, header_style="bold", padding=(0, 1))
    table.add_column(t("plan.column.lottery"), style="bold")
    table.add_column(t("plan.column.cost"), justify="right")
    table.add_column(t("prompt.lottery.days"))
    table.add_column(t("plan.column.weight"), justify="right")
    table.add_column("Pools")

    for lot in settings.lotteries:
        table.add_row(
            lot.label,
            f"{lot.price_per_grid} {lot.currency}",
            ", ".join(i18n.weekday_name(day).capitalize() for day in sorted(lot.draw_days)),
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
        name = str(
            _answer(
                questionary.text(t("prompt.pool.name", number=len(pools) + 1), default="numbers")
            )
        )
        count = str(_answer(questionary.text(t("prompt.pool.count"))))
        maximum = str(_answer(questionary.text(t("prompt.pool.max"))))
        try:
            pools.append(Pool(name=name, count=int(count), maximum=int(maximum)))
        except ValueError as exc:
            _fatal(exc)
        if not _answer(questionary.confirm(t("prompt.pool.another"), default=False)):
            return tuple(pools)


@lottery_app.command("add")
def lottery_add(config_path: ConfigOption = None, lang: LangOption = None) -> None:
    """Add a lottery definition, or replace one with the same label."""
    settings = _load(config_path)
    _apply_language(lang, settings)

    label = str(_answer(questionary.text(t("prompt.lottery.label"))))
    currency = str(_answer(questionary.text(t("prompt.lottery.currency"), default="EUR")))
    price = str(_answer(questionary.text(t("prompt.lottery.price"))))
    days = _answer(
        questionary.checkbox(
            t("prompt.lottery.days"),
            choices=[questionary.Choice(name.capitalize(), value=name) for name in WEEKDAY_NAMES],
        )
    )
    weight = str(_answer(questionary.text(t("prompt.lottery.weight"), default="1.0")))
    pools = _ask_pools()

    try:
        lottery = Lottery(
            label=label,
            currency=currency,
            price_per_grid=money(_clean_amount(price)),
            draw_days=frozenset(WEEKDAY_NAMES.index(day) for day in days),  # type: ignore[union-attr]
            weight=float(weight),
            pools=pools,
        )
    except (InvalidOperation, TypeError, ValueError) as exc:
        _fatal(exc)

    written = config.save(config.with_lottery(settings, lottery), config_path)
    console.print(Text(t("lottery.saved", label=lottery.label, path=written), style="green"))


def _ask_weights(settings: config.Settings, existing: Player | None) -> dict[str, float]:
    """Ask which lotteries someone plays, then how they split their budget."""
    if not settings.lotteries:
        _fatal(t("error.no.lotteries"))

    chosen = _answer(
        questionary.checkbox(
            t("prompt.player.lotteries"),
            choices=[
                questionary.Choice(
                    title=f"{lot.label} — "
                    + t("choice.per.grid", price=lot.price_per_grid, currency=lot.currency),
                    value=lot.label,
                    checked=existing.plays(lot) if existing else True,
                )
                for lot in settings.lotteries
            ],
        )
    )
    if not chosen:
        _fatal(t("error.plays.nothing"))

    console.print()
    console.print(Text(t("player.weight.explain"), style="dim"))
    console.print(Text(t("player.weight.example"), style="dim"))

    weights: dict[str, float] = {}
    for label in chosen:  # type: ignore[union-attr]
        default = existing.weights.get(label, 1.0) if existing else 1.0
        raw = str(
            _answer(questionary.text(t("prompt.weight", label=label), default=f"{default:g}"))
        ).strip()
        try:
            value = float(raw.replace(",", "."))
        except ValueError:
            _fatal(t("error.not.number", value=repr(raw)))
        if value <= 0:
            _fatal(t("error.weight.positive", label=label))
        weights[label] = value
    return weights


@player_app.command("add")
def player_add(config_path: ConfigOption = None, lang: LangOption = None) -> None:
    """Add someone who plays, or update them if the name already exists.

    Everyone keeps their own ceiling and their own lotteries. Configuring a
    second person switches `generate` to household mode, where draws are spread
    across dates so the same game is not played twice on the same day.
    """
    settings = _load(config_path)
    _apply_language(lang, settings)

    name = str(_answer(questionary.text(t("prompt.player.name")))).strip()
    if not name:
        _fatal(t("error.name.empty"))

    existing = settings.find_player(name)
    if existing is not None:
        console.print(Text(t("player.updating", name=existing.name), style="dim"))

    ceiling = str(
        _answer(
            questionary.text(
                t("prompt.player.ceiling", name=name),
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
            max_monthly_budget=money(_clean_amount(ceiling)),
            weights=weights,
        )
    except (InvalidOperation, TypeError, ValueError) as exc:
        _fatal(exc)

    written = config.save(config.with_player(settings, player), config_path)
    console.print(Text(t("player.saved", name=player.name, path=written), style="green"))
    if len(settings.players) == 0:
        console.print(Text(t("player.second.hint"), style="dim"))


@player_app.command("list")
def player_list(config_path: ConfigOption = None, lang: LangOption = None) -> None:
    """Show everyone who plays, with their ceiling and preferences."""
    settings = _load(config_path)
    _apply_language(lang, settings)
    if not settings.players:
        console.print()
        console.print(Text(t("player.none"), style="dim"))
        console.print(Text(t("player.add.hint"), style="dim"))
        console.print()
        return

    table = Table(box=box.ROUNDED, header_style="bold", padding=(0, 1))
    table.add_column(t("plan.column.player"), style="bold magenta")
    table.add_column(t("plan.column.ceiling"), justify="right")
    table.add_column(t("plan.column.plays"))

    for person in settings.players:
        table.add_row(
            person.name,
            str(person.max_monthly_budget),
            ", ".join(
                f"{lot.label} ({person.weight_for(lot):g})"
                for lot in settings.lotteries_for(person)
            )
            or t("plan.player.nothing"),
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
            t(
                "error.player.unknown",
                name=repr(name),
                known=", ".join(p.name for p in settings.players) or t("config.none"),
            )
        )
    written = config.save(config.without_player(settings, name), config_path)
    console.print(Text(t("player.removed", name=name, path=written), style="green"))


@app.command(help=t("version.help"))
def version() -> None:
    """Print the installed version."""
    console.print(f"blindgrid {__version__}")


if __name__ == "__main__":
    app()
