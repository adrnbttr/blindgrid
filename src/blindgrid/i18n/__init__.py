"""Translating the interface.

Plain dictionaries rather than gettext: there is no compilation step, the
catalogues are readable in a diff, and adding a language is one file plus one
line here. A test asserts that every catalogue carries exactly the keys the
English one does, so a missing translation fails the build rather than
surfacing as an English sentence in the middle of a French session.

The language is resolved in this order:

1. ``--lang`` on the command line,
2. ``BLINDGRID_LANG`` in the environment,
3. ``language`` in the configuration file,
4. the system locale,
5. English.

Only the interface is translated. Lottery labels, pool names and player names
come from configuration and are printed exactly as they were written.
"""

from __future__ import annotations

import locale
import os
from typing import Any

from blindgrid.i18n import de, en, es, fr

ENV_VAR = "BLINDGRID_LANG"
DEFAULT = "en"

CATALOGUES: dict[str, dict[str, str]] = {
    "en": en.MESSAGES,
    "fr": fr.MESSAGES,
    "es": es.MESSAGES,
    "de": de.MESSAGES,
}

LANGUAGE_NAMES: dict[str, str] = {
    "en": "English",
    "fr": "Français",
    "es": "Español",
    "de": "Deutsch",
}

_active = DEFAULT


def available() -> tuple[str, ...]:
    """The language codes this build ships, English first."""
    return (DEFAULT, *sorted(code for code in CATALOGUES if code != DEFAULT))


def normalise(code: str | None) -> str | None:
    """Turn ``fr_FR.UTF-8``, ``FR`` or ``fr`` into ``fr``, or ``None``."""
    if not code:
        return None
    base = code.replace("-", "_").split("_")[0].split(".")[0].strip().casefold()
    return base if base in CATALOGUES else None


def from_system() -> str | None:
    """The language the operating system says the user prefers."""
    for variable in ("LC_ALL", "LC_MESSAGES", "LANG", "LANGUAGE"):
        found = normalise(os.environ.get(variable, "").split(":")[0])
        if found:
            return found
    try:
        system, _ = locale.getlocale()
    except ValueError:  # pragma: no cover - depends on a malformed locale
        return None
    return normalise(system)


def resolve(explicit: str | None = None, configured: str | None = None) -> str:
    """Pick the language to use, following the documented order."""
    for candidate in (explicit, os.environ.get(ENV_VAR), configured):
        found = normalise(candidate)
        if found:
            return found
    return from_system() or DEFAULT


def activate(code: str) -> str:
    """Set the language for the rest of the process. Returns what was set."""
    global _active  # noqa: PLW0603 - a process-wide setting is exactly what this is
    _active = normalise(code) or DEFAULT
    return _active


def current() -> str:
    return _active


def t(key: str, **params: Any) -> str:
    """Translate ``key``, falling back to English and then to the key itself.

    A key that reaches the caller unchanged is a bug, but printing it beats
    raising in the middle of someone's monthly plan.
    """
    catalogue = CATALOGUES.get(_active, CATALOGUES[DEFAULT])
    template = catalogue.get(key) or CATALOGUES[DEFAULT].get(key) or key
    if not params:
        return template
    try:
        return template.format(**params)
    except (IndexError, KeyError):  # pragma: no cover - guards a malformed catalogue
        return template


def month_name(month: int) -> str:
    """The month's name in the active language."""
    return t(f"month.{month}")


def weekday_name(weekday: int) -> str:
    """The weekday's name in the active language, Monday being 0."""
    return t(f"weekday.{weekday}")


def weekday_short(weekday: int) -> str:
    """The weekday abbreviated the way the language does it.

    Not a truncation: German writes Mi, not Mit.
    """
    return t(f"weekday.short.{weekday}")
