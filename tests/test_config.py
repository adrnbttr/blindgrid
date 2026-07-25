"""Configuration parsing, validation and round-tripping."""

from __future__ import annotations

import tomllib
from decimal import Decimal
from pathlib import Path

import pytest

from blindgrid import config
from blindgrid.errors import ConfigError
from blindgrid.models import Lottery, Pool

MINIMAL = """
max_monthly_budget = 30.00
export_path = "out/plan.md"

[[lottery]]
label = "Powerball"
currency = "USD"
price_per_grid = 2.00
draw_days = ["monday", "wednesday", "saturday"]
weight = 1.5

  [[lottery.pool]]
  name = "numbers"
  count = 5
  max = 69

  [[lottery.pool]]
  name = "powerball"
  count = 1
  max = 26
"""


def parse(text: str) -> config.Settings:
    return config.parse(tomllib.loads(text))


def test_parses_a_lottery_from_another_country() -> None:
    settings = parse(MINIMAL)
    (lottery,) = settings.lotteries

    assert settings.max_monthly_budget == Decimal("30.00")
    assert settings.export_path == Path("out/plan.md")
    assert lottery.label == "Powerball"
    assert lottery.currency == "USD"
    assert lottery.price_per_grid == Decimal("2.00")
    assert lottery.draw_days == frozenset({0, 2, 5})
    assert lottery.weight == 1.5
    assert lottery.pools == (Pool("numbers", 5, 69), Pool("powerball", 1, 26))


def test_all_filters_are_enabled_by_default() -> None:
    assert parse(MINIMAL).enabled_filters == config.DEFAULT_ENABLED


def test_filters_can_be_switched_off() -> None:
    settings = parse(MINIMAL + "\n[filters]\nmixed_parity = false\n")
    assert "mixed_parity" not in settings.enabled_filters
    assert "central_sum" in settings.enabled_filters


def test_an_unknown_filter_is_rejected() -> None:
    with pytest.raises(ConfigError, match="unknown rule"):
        parse(MINIMAL + "\n[filters]\nlucky_numbers = true\n")


@pytest.mark.parametrize(
    "removed",
    ['draw_days = ["monday", "wednesday", "saturday"]', "price_per_grid = 2.00"],
)
def test_a_missing_required_key_is_reported(removed: str) -> None:
    key = removed.split(" =", maxsplit=1)[0]
    with pytest.raises(ConfigError, match=key):
        parse(MINIMAL.replace(removed, ""))


def test_an_invalid_weekday_names_the_valid_ones() -> None:
    with pytest.raises(ConfigError, match="is not a weekday"):
        parse(MINIMAL.replace('"monday"', '"lundi"'))


def test_a_pool_larger_than_its_range_is_rejected() -> None:
    with pytest.raises(ConfigError, match="must be at least"):
        parse(MINIMAL.replace("count = 5\n  max = 69", "count = 70\n  max = 69"))


def test_a_lottery_without_a_pool_is_rejected() -> None:
    text = MINIMAL.split("  [[lottery.pool]]", maxsplit=1)[0]
    with pytest.raises(ConfigError, match="missing required key 'pool'"):
        parse(text)


def test_an_empty_pool_list_is_rejected() -> None:
    with pytest.raises(ConfigError, match="at least one"):
        parse(MINIMAL.split("  [[lottery.pool]]", maxsplit=1)[0] + "\n  pool = []\n")


def test_a_negative_weight_is_rejected() -> None:
    with pytest.raises(ConfigError, match="weight"):
        parse(MINIMAL.replace("weight = 1.5", "weight = -1.0"))


def test_a_missing_file_explains_how_to_create_one(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="config init"):
        config.load(tmp_path / "absent.toml")


def test_malformed_toml_is_reported(tmp_path: Path) -> None:
    broken = tmp_path / "config.toml"
    broken.write_text("max_monthly_budget = = 3", encoding="utf-8")
    with pytest.raises(ConfigError, match="invalid TOML"):
        config.load(broken)


def test_settings_survive_a_save_and_reload(tmp_path: Path) -> None:
    original = parse(MINIMAL + "\n[filters]\nmixed_parity = false\n")
    target = config.save(original, tmp_path / "nested" / "config.toml")
    reloaded = config.load(target)

    assert reloaded.max_monthly_budget == original.max_monthly_budget
    assert reloaded.export_path == original.export_path
    assert reloaded.enabled_filters == original.enabled_filters
    assert reloaded.lotteries == original.lotteries


def test_the_shipped_example_is_valid() -> None:
    settings = config.parse(tomllib.loads(config.example_toml()))
    assert len(settings.lotteries) == 3
    assert settings.max_monthly_budget > 0
    assert all(lottery.pools for lottery in settings.lotteries)


def test_enabled_lotteries_skips_zero_weight() -> None:
    settings = parse(MINIMAL.replace("weight = 1.5", "weight = 0.0"))
    assert settings.lotteries
    assert settings.enabled_lotteries() == ()


def test_lookup_is_case_insensitive() -> None:
    settings = parse(MINIMAL)
    assert settings.find("powerball") is not None
    assert settings.find("PowerBall") is not None
    assert settings.find("Loto") is None


def test_adding_a_lottery_appends_it() -> None:
    settings = parse(MINIMAL)
    extra = Lottery(
        label="Loto",
        currency="EUR",
        price_per_grid=Decimal("2.20"),
        draw_days=frozenset({0}),
        weight=1.0,
        pools=(Pool("numbers", 5, 49),),
    )
    updated = config.with_lottery(settings, extra)
    assert [lot.label for lot in updated.lotteries] == ["Powerball", "Loto"]


def test_adding_an_existing_label_replaces_it_in_place() -> None:
    settings = parse(MINIMAL)
    replacement = Lottery(
        label="Powerball",
        currency="USD",
        price_per_grid=Decimal("3.00"),
        draw_days=frozenset({0}),
        weight=2.0,
        pools=(Pool("numbers", 5, 69),),
    )
    updated = config.with_lottery(settings, replacement)

    assert len(updated.lotteries) == 1
    assert updated.lotteries[0].price_per_grid == Decimal("3.00")


def test_the_env_var_overrides_the_lookup(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    target = tmp_path / "elsewhere.toml"
    monkeypatch.setenv(config.ENV_VAR, str(target))
    assert config.default_path() == target
