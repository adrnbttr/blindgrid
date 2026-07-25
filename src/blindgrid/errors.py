"""Exceptions raised by blindgrid.

The CLI catches :class:`BlindgridError` and prints the message without a
traceback, so every subclass message must be readable by an end user.
"""

from __future__ import annotations


class BlindgridError(Exception):
    """Base class for every error this tool raises on purpose."""


class ConfigError(BlindgridError):
    """The configuration file is missing, malformed or internally inconsistent."""


class BudgetError(BlindgridError):
    """The requested budget is invalid or exceeds the configured hard ceiling."""


class GridGenerationError(BlindgridError):
    """No grid satisfying the active filters was found within the attempt cap."""
