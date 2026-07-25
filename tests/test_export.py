"""Markdown export."""

from __future__ import annotations

import random
from decimal import Decimal
from pathlib import Path

import pytest

from blindgrid.export import export_plan, to_markdown
from blindgrid.models import Lottery, Plan
from blindgrid.plan import build_plan


@pytest.fixture
def plan(lotteries: tuple[Lottery, ...], rng: random.Random) -> Plan:
    return build_plan(budget=Decimal("40.00"), lotteries=lotteries, year=2026, month=9, rng=rng)


def test_contains_every_draw(plan: Plan) -> None:
    document = to_markdown(plan)
    for draw in plan.draws:
        assert draw.draw_date.isoformat() in document
        assert draw.lottery.label in document


def test_contains_the_totals_and_the_disclaimer(plan: Plan) -> None:
    document = to_markdown(plan)
    assert f"{plan.total_committed:.2f}" in document
    assert f"{plan.unspent:.2f}" in document
    assert "not predictions" in document


def test_names_the_month(plan: Plan) -> None:
    assert "September 2026" in to_markdown(plan)


def test_export_is_overwritten_never_appended(plan: Plan, tmp_path: Path) -> None:
    target = tmp_path / "plan.md"
    target.write_text("previous run\n" * 100, encoding="utf-8")

    export_plan(plan, target)
    content = target.read_text(encoding="utf-8")

    assert "previous run" not in content
    assert content == to_markdown(plan)


def test_export_creates_missing_directories(plan: Plan, tmp_path: Path) -> None:
    target = tmp_path / "deep" / "nested" / "plan.md"
    assert export_plan(plan, target).exists()


def test_an_empty_plan_still_produces_a_document(
    lotteries: tuple[Lottery, ...], rng: random.Random
) -> None:
    empty = build_plan(budget=Decimal("1.00"), lotteries=lotteries, year=2026, month=9, rng=rng)
    document = to_markdown(empty)
    assert "No draw could be planned" in document
