"""Regenerate ``docs/demo.svg`` from a real run.

The image in the README is not a mockup: it is the actual output of
:func:`blindgrid.plan.build_plan`, recorded by rich and written straight to
SVG. Run this after any change to the rendering.

    python docs/make_demo.py
"""

from __future__ import annotations

import sys
import tomllib
from decimal import Decimal
from pathlib import Path

from rich.console import Console
from rich.text import Text

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from blindgrid import config  # noqa: E402
from blindgrid.generator import system_rng  # noqa: E402
from blindgrid.plan import build_plan  # noqa: E402
from blindgrid.render import render_plan  # noqa: E402

OUTPUT = ROOT / "docs" / "demo.svg"
BUDGET = Decimal("30.00")
YEAR, MONTH = 2026, 9


def main() -> None:
    settings = config.parse(tomllib.loads(config.example_toml()))
    console = Console(record=True, width=98, file=open("/dev/null", "w"))  # noqa: SIM115

    console.print()
    console.print(Text("$ blindgrid generate", style="bold green"))
    console.print()
    console.print(Text("? Budget for this month?  30", style="cyan"))
    console.print(
        Text("? Which lotteries do you want to include?  EuroMillions, Loto", style="cyan")
    )

    plan = build_plan(
        budget=BUDGET,
        lotteries=settings.enabled_lotteries()[:2],
        year=YEAR,
        month=MONTH,
        rng=system_rng(),
        enabled_filters=settings.enabled_filters,
    )
    render_plan(plan, console)
    console.print(Text("Exported to plan.md", style="dim"))
    console.print()

    console.save_svg(str(OUTPUT), title="blindgrid")
    print(f"Wrote {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
