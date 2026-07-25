"""Reading and writing the TOML configuration.

Configuration is the only place a specific lottery is ever named. Everything
the tool knows about a game — its price, its draw days, the shape of its pools
— comes from here, which is what makes the code portable to any country.

Resolution order for the config file:

1. the ``BLINDGRID_CONFIG`` environment variable,
2. ``config.toml`` in the current directory,
3. ``~/.config/blindgrid/config.toml``.
"""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass, replace
from decimal import Decimal, InvalidOperation
from importlib import resources
from pathlib import Path
from typing import Any

import tomli_w

from blindgrid import i18n, paths
from blindgrid.errors import ConfigError
from blindgrid.filters import DEFAULT_ENABLED, RULE_NAMES
from blindgrid.models import WEEKDAY_NAMES, Lottery, Player, Pool, money

CONFIG_FILENAME = "config.toml"
EXAMPLE_FILENAME = "config.example.toml"
ENV_VAR = "BLINDGRID_CONFIG"

DEFAULT_MAX_MONTHLY_BUDGET = Decimal("50.00")
DEFAULT_EXPORT_PATH = Path("plan.md")


@dataclass(frozen=True, slots=True)
class Settings:
    """The whole configuration, validated."""

    max_monthly_budget: Decimal
    export_path: Path
    enabled_filters: frozenset[str]
    lotteries: tuple[Lottery, ...]
    players: tuple[Player, ...] = ()
    language: str | None = None
    path: Path | None = None

    def enabled_lotteries(self) -> tuple[Lottery, ...]:
        """Lotteries with a non-zero weight, in configuration order."""
        return tuple(lottery for lottery in self.lotteries if lottery.is_enabled)

    def find(self, label: str) -> Lottery | None:
        """Look up a lottery by label, case-insensitively."""
        wanted = label.casefold()
        return next((lot for lot in self.lotteries if lot.label.casefold() == wanted), None)

    def find_player(self, name: str) -> Player | None:
        """Look up a player by name, case-insensitively."""
        wanted = name.casefold()
        return next((p for p in self.players if p.name.casefold() == wanted), None)

    @property
    def is_household(self) -> bool:
        """Whether players are configured, which switches ``generate`` modes."""
        return bool(self.players)

    def lotteries_for(self, player: Player) -> tuple[Lottery, ...]:
        """The lotteries ``player`` actually plays, in configuration order."""
        return tuple(lottery for lottery in self.lotteries if player.plays(lottery))


def default_path() -> Path:
    """The config file this run will read, whether or not it exists yet."""
    override = os.environ.get(ENV_VAR)
    if override:
        return Path(override).expanduser()
    local = Path.cwd() / CONFIG_FILENAME
    if local.exists():
        return local
    return paths.config_dir() / CONFIG_FILENAME


def example_toml() -> str:
    """The contents of the shipped ``config.example.toml``.

    Installed copies read it from the package; a source checkout falls back to
    the file at the repository root, which is the same file.
    """
    packaged = resources.files("blindgrid") / "data" / EXAMPLE_FILENAME
    if packaged.is_file():
        return packaged.read_text(encoding="utf-8")

    checkout = Path(__file__).resolve().parents[2] / EXAMPLE_FILENAME
    if checkout.is_file():
        return checkout.read_text(encoding="utf-8")

    raise ConfigError(f"{EXAMPLE_FILENAME} is missing from this installation")


def _require(table: dict[str, Any], key: str, context: str) -> Any:
    if key not in table:
        raise ConfigError(f"{context}: missing required key {key!r}")
    return table[key]


def _as_decimal(value: Any, context: str) -> Decimal:
    try:
        amount = money(value)
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ConfigError(f"{context}: {value!r} is not a valid amount") from exc
    return amount


def _parse_weekday(name: Any, context: str) -> int:
    if not isinstance(name, str) or name.casefold() not in WEEKDAY_NAMES:
        raise ConfigError(
            f"{context}: {name!r} is not a weekday. Expected one of: {', '.join(WEEKDAY_NAMES)}"
        )
    return WEEKDAY_NAMES.index(name.casefold())


def _parse_pool(table: dict[str, Any], context: str) -> Pool:
    try:
        return Pool(
            name=str(_require(table, "name", context)),
            count=int(_require(table, "count", context)),
            maximum=int(_require(table, "max", context)),
        )
    except (TypeError, ValueError) as exc:
        raise ConfigError(f"{context}: {exc}") from exc


def _parse_lottery(table: dict[str, Any], index: int) -> Lottery:
    label = table.get("label", f"#{index + 1}")
    context = f"lottery {label!r}"

    pool_tables = _require(table, "pool", context)
    if not isinstance(pool_tables, list) or not pool_tables:
        raise ConfigError(f"{context}: at least one [[lottery.pool]] is required")
    pools = tuple(
        _parse_pool(pool, f"{context}, pool {n + 1}") for n, pool in enumerate(pool_tables)
    )

    days = _require(table, "draw_days", context)
    if not isinstance(days, list) or not days:
        raise ConfigError(f"{context}: draw_days must be a non-empty list")

    try:
        return Lottery(
            label=str(label),
            currency=str(table.get("currency", "EUR")),
            price_per_grid=_as_decimal(
                _require(table, "price_per_grid", context), f"{context}, price_per_grid"
            ),
            draw_days=frozenset(_parse_weekday(day, f"{context}, draw_days") for day in days),
            weight=float(table.get("weight", 1.0)),
            pools=pools,
        )
    except (TypeError, ValueError) as exc:
        raise ConfigError(f"{context}: {exc}") from exc


def _parse_player(table: dict[str, Any], index: int, known: set[str]) -> Player:
    name = table.get("name", f"#{index + 1}")
    context = f"player {name!r}"

    weights = table.get("weight", {})
    if not isinstance(weights, dict):
        raise ConfigError(f"{context}: [player.weight] must be a table of lottery = number")

    unknown = set(weights) - known
    if unknown:
        raise ConfigError(
            f"{context}: unknown lottery in [player.weight]: {', '.join(sorted(unknown))}. "
            f"Configured: {', '.join(sorted(known))}"
        )

    try:
        return Player(
            name=str(name),
            max_monthly_budget=_as_decimal(
                _require(table, "max_monthly_budget", context),
                f"{context}, max_monthly_budget",
            ),
            weights={label: float(weight) for label, weight in weights.items()},
        )
    except (TypeError, ValueError) as exc:
        raise ConfigError(f"{context}: {exc}") from exc


def _parse_filters(table: dict[str, Any]) -> frozenset[str]:
    unknown = set(table) - set(RULE_NAMES)
    if unknown:
        raise ConfigError(
            f"[filters]: unknown rule(s) {', '.join(sorted(unknown))}. "
            f"Known rules: {', '.join(RULE_NAMES)}"
        )
    return frozenset(name for name in RULE_NAMES if table.get(name, True))


def _parse_language(value: Any) -> str | None:
    """Validate the configured language, if any."""
    if value is None:
        return None
    code = i18n.normalise(str(value))
    if code is None:
        raise ConfigError(
            f"language: {value!r} is not available. Known: {', '.join(i18n.available())}"
        )
    return code


def parse(data: dict[str, Any], path: Path | None = None) -> Settings:
    """Build :class:`Settings` from an already decoded TOML mapping."""
    lottery_tables = data.get("lottery", [])
    if not isinstance(lottery_tables, list):
        raise ConfigError("[[lottery]] must be an array of tables")

    filters = data.get("filters", {})
    if not isinstance(filters, dict):
        raise ConfigError("[filters] must be a table")

    player_tables = data.get("player", [])
    if not isinstance(player_tables, list):
        raise ConfigError("[[player]] must be an array of tables")

    lotteries = tuple(_parse_lottery(table, index) for index, table in enumerate(lottery_tables))
    known = {lottery.label for lottery in lotteries}
    players = tuple(_parse_player(table, index, known) for index, table in enumerate(player_tables))

    duplicates = {p.name for p in players if sum(q.name == p.name for q in players) > 1}
    if duplicates:
        raise ConfigError(f"duplicate player name(s): {', '.join(sorted(duplicates))}")

    return Settings(
        max_monthly_budget=_as_decimal(
            data.get("max_monthly_budget", DEFAULT_MAX_MONTHLY_BUDGET), "max_monthly_budget"
        ),
        export_path=Path(str(data.get("export_path", DEFAULT_EXPORT_PATH))).expanduser(),
        language=_parse_language(data.get("language")),
        enabled_filters=_parse_filters(filters) if filters else DEFAULT_ENABLED,
        lotteries=lotteries,
        players=players,
        path=path,
    )


def load(path: Path | None = None) -> Settings:
    """Read and validate the configuration file."""
    target = path or default_path()
    if not target.exists():
        raise ConfigError(
            f"No configuration found at {target}.\n"
            f"Copy {EXAMPLE_FILENAME} to {CONFIG_FILENAME}, or run 'blindgrid config init'."
        )
    try:
        with target.open("rb") as handle:
            data = tomllib.load(handle)
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"{target}: invalid TOML ({exc})") from exc
    return parse(data, path=target)


def to_dict(settings: Settings) -> dict[str, Any]:
    """Render :class:`Settings` back into a TOML-serialisable mapping."""
    return {
        "max_monthly_budget": float(settings.max_monthly_budget),
        "export_path": str(settings.export_path),
        **({"language": settings.language} if settings.language else {}),
        "filters": {name: name in settings.enabled_filters for name in RULE_NAMES},
        "lottery": [
            {
                "label": lottery.label,
                "currency": lottery.currency,
                "price_per_grid": float(lottery.price_per_grid),
                "draw_days": [WEEKDAY_NAMES[day] for day in sorted(lottery.draw_days)],
                "weight": lottery.weight,
                "pool": [
                    {"name": pool.name, "count": pool.count, "max": pool.maximum}
                    for pool in lottery.pools
                ],
            }
            for lottery in settings.lotteries
        ],
        "player": [
            {
                "name": player.name,
                "max_monthly_budget": float(player.max_monthly_budget),
                "weight": dict(player.weights),
            }
            for player in settings.players
        ],
    }


def save(settings: Settings, path: Path | None = None) -> Path:
    """Write ``settings`` to disk, creating parent directories as needed.

    Comments in the existing file are not preserved: the file is regenerated
    from the validated settings.
    """
    target = path or settings.path or default_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("wb") as handle:
        tomli_w.dump(to_dict(settings), handle)
    return target


def with_lottery(settings: Settings, lottery: Lottery) -> Settings:
    """Return a copy of ``settings`` with ``lottery`` added or replaced by label."""
    existing = settings.find(lottery.label)
    if existing is None:
        return replace(settings, lotteries=(*settings.lotteries, lottery))
    return replace(
        settings,
        lotteries=tuple(lottery if lot is existing else lot for lot in settings.lotteries),
    )


def with_player(settings: Settings, player: Player) -> Settings:
    """Return a copy of ``settings`` with ``player`` added or replaced by name."""
    existing = settings.find_player(player.name)
    if existing is None:
        return replace(settings, players=(*settings.players, player))
    return replace(
        settings,
        players=tuple(player if p is existing else p for p in settings.players),
    )


def without_player(settings: Settings, name: str) -> Settings:
    """Return a copy of ``settings`` with the named player removed."""
    return replace(
        settings,
        players=tuple(p for p in settings.players if p.name.casefold() != name.casefold()),
    )
