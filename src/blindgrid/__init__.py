"""blindgrid — lottery grids from cryptographic randomness, inside a hard budget.

This package does not predict anything, and no part of it should ever try to.
Lottery draws are independent events: no combination is more likely than any
other, and no amount of code changes that. What the tool does is remove human
bias from number selection and make the monthly gambling budget explicit and
capped.
"""

from __future__ import annotations

__version__ = "0.2.1"
__all__ = ["__version__"]
