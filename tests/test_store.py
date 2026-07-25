"""Saving and reloading the current month's plan."""

from __future__ import annotations

import json
import random
from datetime import datetime
from decimal import Decimal
from pathlib import Path

import pytest

from blindgrid import store
from blindgrid.errors import StoreError
from blindgrid.models import Lottery, Plan
from blindgrid.plan import build_plan


@pytest.fixture
def plan(lotteries: tuple[Lottery, ...], rng: random.Random) -> Plan:
    return build_plan(budget=Decimal("40.00"), lotteries=lotteries, year=2026, month=9, rng=rng)


@pytest.fixture
def state_file(tmp_path: Path) -> Path:
    return tmp_path / "state" / "plan.json"


def test_a_saved_plan_comes_back_identical(plan: Plan, state_file: Path) -> None:
    store.save(plan, state_file)
    stored = store.load(state_file)

    assert stored is not None
    assert stored.plan == plan


def test_every_number_survives_the_round_trip(plan: Plan, state_file: Path) -> None:
    store.save(plan, state_file)
    reloaded = store.load(state_file).plan

    original = [(d.draw_date, d.lottery.label, g.numbers) for d in plan.draws for g in d.grids]
    returned = [(d.draw_date, d.lottery.label, g.numbers) for d in reloaded.draws for g in d.grids]
    assert original == returned


def test_money_keeps_its_precision(plan: Plan, state_file: Path) -> None:
    store.save(plan, state_file)
    reloaded = store.load(state_file).plan

    assert reloaded.budget == plan.budget
    assert reloaded.total_committed == plan.total_committed
    assert reloaded.unspent == plan.unspent
    assert [a.share for a in reloaded.allocations] == [a.share for a in plan.allocations]


def test_the_moment_of_drawing_is_kept(plan: Plan, state_file: Path) -> None:
    when = datetime(2026, 9, 1, 8, 30, 0)
    store.save(plan, state_file, drawn_on=when)
    assert store.load(state_file).drawn_on == when


def test_nothing_saved_yet_is_not_an_error(state_file: Path) -> None:
    assert store.load(state_file) is None


def test_saving_creates_missing_directories(plan: Plan, tmp_path: Path) -> None:
    target = tmp_path / "deep" / "nested" / "plan.json"
    assert store.save(plan, target).exists()


def test_a_new_month_replaces_the_old_one(
    plan: Plan, lotteries: tuple[Lottery, ...], rng: random.Random, state_file: Path
) -> None:
    store.save(plan, state_file)
    october = build_plan(budget=Decimal("20.00"), lotteries=lotteries, year=2026, month=10, rng=rng)
    store.save(october, state_file)

    # One file, one plan. No history accumulates.
    assert store.load(state_file).plan.month == 10
    assert list(state_file.parent.iterdir()) == [state_file]


def test_load_for_matches_only_its_own_month(plan: Plan, state_file: Path) -> None:
    store.save(plan, state_file)

    assert store.load_for(2026, 9, state_file) is not None
    assert store.load_for(2026, 10, state_file) is None
    assert store.load_for(2025, 9, state_file) is None


def test_the_snapshot_is_self_contained(plan: Plan, state_file: Path) -> None:
    """A stored plan carries its lotteries, so later config edits cannot alter it."""
    store.save(plan, state_file)
    reloaded = store.load(state_file).plan

    for allocation, original in zip(reloaded.allocations, plan.allocations, strict=True):
        assert allocation.lottery == original.lottery
        assert allocation.lottery.pools == original.lottery.pools
        assert allocation.lottery.draw_days == original.lottery.draw_days


def test_a_corrupt_file_is_reported_not_swallowed(state_file: Path) -> None:
    state_file.parent.mkdir(parents=True)
    state_file.write_text("{not json", encoding="utf-8")

    with pytest.raises(StoreError):
        store.load(state_file)


def test_a_truncated_plan_is_reported(plan: Plan, state_file: Path) -> None:
    store.save(plan, state_file)
    data = json.loads(state_file.read_text())
    del data["draws"]
    state_file.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(StoreError, match="malformed"):
        store.load(state_file)


def test_a_future_format_is_refused_rather_than_misread(plan: Plan, state_file: Path) -> None:
    store.save(plan, state_file)
    data = json.loads(state_file.read_text())
    data["schema"] = store.SCHEMA_VERSION + 1
    state_file.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(StoreError, match="format version"):
        store.load(state_file)


def test_clear_removes_the_plan(plan: Plan, state_file: Path) -> None:
    store.save(plan, state_file)
    assert store.clear(state_file) is True
    assert store.load(state_file) is None
    assert store.clear(state_file) is False


def test_the_env_var_overrides_the_location(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "elsewhere.json"
    monkeypatch.setenv(store.ENV_VAR, str(target))
    assert store.default_path() == target


def test_the_default_location_follows_the_platform(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Where the state directory is depends on the OS; test_paths.py owns that.

    Here we only check that the store defers to it rather than hardcoding a
    layout of its own — which is what made this test fail on Windows before
    paths.py existed.
    """
    monkeypatch.delenv(store.ENV_VAR, raising=False)
    monkeypatch.setattr(store.paths, "state_dir", lambda: tmp_path / "somewhere")
    assert store.default_path() == tmp_path / "somewhere" / "plan.json"
