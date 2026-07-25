"""Translation: catalogue completeness, resolution order, and rendering.

The completeness tests are the important ones. A missing key does not crash,
it silently falls back to English, which is exactly the kind of defect that
ships unnoticed — so it fails the build here instead.
"""

from __future__ import annotations

import random
import string
from decimal import Decimal

import pytest
from rich.console import Console

from blindgrid import i18n
from blindgrid.i18n import en
from blindgrid.models import Lottery, Plan
from blindgrid.plan import build_plan
from blindgrid.render import render_plan

OTHERS = [code for code in i18n.CATALOGUES if code != "en"]


@pytest.fixture
def plan(lotteries: tuple[Lottery, ...], rng: random.Random) -> Plan:
    return build_plan(budget=Decimal("40.00"), lotteries=lotteries, year=2026, month=9, rng=rng)


@pytest.mark.parametrize("code", OTHERS)
def test_every_catalogue_covers_the_english_one(code: str) -> None:
    missing = sorted(set(en.MESSAGES) - set(i18n.CATALOGUES[code]))
    assert not missing, f"{code} is missing: {', '.join(missing)}"


@pytest.mark.parametrize("code", OTHERS)
def test_no_catalogue_carries_keys_english_does_not(code: str) -> None:
    """A stray key is a typo, or a message nobody else translates."""
    extra = sorted(set(i18n.CATALOGUES[code]) - set(en.MESSAGES))
    assert not extra, f"{code} has unknown keys: {', '.join(extra)}"


@pytest.mark.parametrize("code", list(i18n.CATALOGUES))
def test_placeholders_match_the_english_message(code: str) -> None:
    """A translation that drops or renames a placeholder formats to nonsense."""
    formatter = string.Formatter()

    def fields(template: str) -> set[str]:
        return {name for _, name, _, _ in formatter.parse(template) if name}

    for key, english in en.MESSAGES.items():
        translated = i18n.CATALOGUES[code][key]
        assert fields(translated) == fields(english), f"{code}:{key}"


@pytest.mark.parametrize("code", list(i18n.CATALOGUES))
def test_every_catalogue_has_all_months_and_weekdays(code: str) -> None:
    catalogue = i18n.CATALOGUES[code]
    assert all(f"month.{n}" in catalogue for n in range(1, 13))
    assert all(f"weekday.{n}" in catalogue for n in range(7))


@pytest.mark.parametrize("code", list(i18n.CATALOGUES))
def test_nothing_is_left_untranslated(code: str) -> None:
    """Catch a catalogue copied from English and only half edited."""
    if code == "en":
        return
    catalogue = i18n.CATALOGUES[code]
    identical = [
        key
        for key, text in catalogue.items()
        # Column labels legitimately coincide across languages ("Budget",
        # "Date"), as do the option names quoted inside error messages.
        if text == en.MESSAGES[key] and len(text.split()) > 3
    ]
    assert not identical, f"{code} looks untranslated for: {', '.join(identical)}"


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("fr", "fr"),
        ("FR", "fr"),
        ("fr_FR", "fr"),
        ("fr-FR", "fr"),
        ("fr_FR.UTF-8", "fr"),
        ("de_DE.utf8", "de"),
        ("es", "es"),
        ("", None),
        (None, None),
        ("klingon", None),
        ("zz_ZZ", None),
    ],
)
def test_locale_strings_are_normalised(value: str | None, expected: str | None) -> None:
    assert i18n.normalise(value) == expected


def test_the_explicit_choice_wins(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(i18n.ENV_VAR, "de")
    assert i18n.resolve("fr", configured="es") == "fr"


def test_the_environment_beats_the_config(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(i18n.ENV_VAR, "de")
    assert i18n.resolve(None, configured="es") == "de"


def test_the_config_beats_the_system(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(i18n.ENV_VAR, raising=False)
    monkeypatch.setenv("LANG", "de_DE.UTF-8")
    assert i18n.resolve(None, configured="es") == "es"


def test_the_system_locale_is_the_last_resort(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(i18n.ENV_VAR, raising=False)
    for variable in ("LC_ALL", "LC_MESSAGES", "LANGUAGE"):
        monkeypatch.delenv(variable, raising=False)
    monkeypatch.setenv("LANG", "es_ES.UTF-8")
    assert i18n.resolve() == "es"


def test_an_unknown_locale_falls_back_to_english(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(i18n.ENV_VAR, raising=False)
    for variable in ("LC_ALL", "LC_MESSAGES", "LANGUAGE"):
        monkeypatch.delenv(variable, raising=False)
    monkeypatch.setenv("LANG", "kl_KL.UTF-8")
    # getlocale() would otherwise report the locale of whoever runs the suite.
    monkeypatch.setattr(i18n.locale, "getlocale", lambda: (None, None))
    assert i18n.resolve() == "en"


def test_an_unknown_language_does_not_activate(monkeypatch: pytest.MonkeyPatch) -> None:
    assert i18n.activate("klingon") == "en"
    assert i18n.current() == "en"


def test_an_unknown_key_returns_itself() -> None:
    i18n.activate("fr")
    assert i18n.t("no.such.key") == "no.such.key"
    i18n.activate("en")


def test_translation_substitutes_parameters() -> None:
    i18n.activate("fr")
    assert "Marie" in i18n.t("prompt.budget.player", name="Marie")
    i18n.activate("en")


@pytest.mark.parametrize("code", list(i18n.CATALOGUES))
def test_months_and_weekdays_render(code: str) -> None:
    i18n.activate(code)
    try:
        assert all(i18n.month_name(n) for n in range(1, 13))
        assert all(i18n.weekday_name(n) for n in range(7))
        assert i18n.month_name(9) != "month.9"
    finally:
        i18n.activate("en")


def test_a_plan_renders_in_french(plan: Plan) -> None:
    i18n.activate("fr")
    try:
        console = Console(width=130, no_color=True)
        with console.capture() as captured:
            render_plan(plan, console)
        output = captured.get()
    finally:
        i18n.activate("en")

    assert "Tirages à jouer" in output
    assert "septembre 2026" in output
    assert "Répartition du budget" in output
    assert "Les tirages sont des événements indépendants" in output
    assert "Draws to play" not in output


@pytest.mark.parametrize("code", OTHERS)
def test_a_plan_renders_in_every_language(code: str, plan: Plan) -> None:
    """Whatever the language, the table is built without an untranslated key."""
    i18n.activate(code)
    try:
        console = Console(width=130, no_color=True)
        with console.capture() as captured:
            render_plan(plan, console)
        output = captured.get()
    finally:
        i18n.activate("en")

    assert "plan.title" not in output
    assert "plan.column" not in output
    assert "2026" in output


def test_english_is_listed_first() -> None:
    assert i18n.available()[0] == "en"
    assert set(i18n.available()) == set(i18n.CATALOGUES)


def test_every_language_has_a_display_name() -> None:
    assert set(i18n.LANGUAGE_NAMES) == set(i18n.CATALOGUES)
