"""English messages. This catalogue is the reference: every other one must
carry exactly these keys, which ``tests/test_i18n.py`` enforces."""

from __future__ import annotations

MESSAGES: dict[str, str] = {
    # Commands and help
    "app.help": (
        "Generate lottery grids from cryptographic randomness and plan a month "
        "within a hard budget cap. This tool predicts nothing."
    ),
    "generate.help": "Build this month's plan: how much to spend, which draws, which numbers.",
    "config.help": "Inspect and edit the configuration.",
    "lottery.help": "Manage lottery definitions.",
    "player.help": "Manage the people who play.",
    "version.help": "Print the installed version.",
    "config.init.help": "Create a configuration file from the shipped example.",
    "config.show.help": "Print the active configuration.",
    "config.edit.help": "Walk through the configuration values one by one.",
    "lottery.list.help": "Show every configured lottery.",
    "lottery.add.help": "Add a lottery definition, or replace one with the same label.",
    "player.add.help": "Add someone who plays, or update them if the name already exists.",
    "player.list.help": "Show everyone who plays, with their ceiling and preferences.",
    "player.remove.help": "Remove someone. Only their configuration goes.",
    "option.force.init": "Overwrite an existing configuration.",
    "argument.player.name": "Who to remove.",
    "option.config": "Path to the configuration file.",
    "option.budget": "Budget to use. With players configured: NAME=AMOUNT, repeatable.",
    "option.lottery": "Include this lottery. Repeatable. Single-player mode only.",
    "option.player": "Limit the plan to these players. Repeatable.",
    "option.month": "Month to plan, as YYYY-MM. Defaults to now.",
    "option.force": "Draw a new plan even if this month already has one.",
    "option.export": "Write the Markdown export.",
    "option.compact": "Force the narrow layout, or the table. Default: fit to the terminal.",
    "option.lang": "Language for this run.",
    # Prompts
    "prompt.budget": "Budget for this month?",
    "prompt.budget.player": "Budget for {name}? (blank to sit this month out)",
    "prompt.lotteries": "Which lotteries do you want to include?",
    "prompt.player.lotteries": "Which lotteries does this person play?",
    "prompt.player.name": "Name?",
    "prompt.player.ceiling": "Hard monthly ceiling for {name}?",
    "prompt.weight": "Weight for {label}?",
    "prompt.ceiling": "Hard monthly ceiling?",
    "prompt.export": "Export the plan to?",
    "prompt.filters": "Active anti-pattern filters",
    "prompt.language": "Language?",
    "prompt.lottery.label": "Label?",
    "prompt.lottery.currency": "Currency?",
    "prompt.lottery.price": "Price per grid?",
    "prompt.lottery.days": "Draw days",
    "prompt.lottery.weight": "Weight? (relative share, 0 disables)",
    "prompt.pool.name": "Pool {number} name?",
    "prompt.pool.count": "How many numbers are drawn?",
    "prompt.pool.max": "Drawn from 1 to?",
    "prompt.pool.another": "Add another pool?",
    "choice.per.grid": "{price} {currency} per grid",
    "choice.per.grid.weight": "{price} {currency} per grid, weight {weight}",
    # Plan output
    "plan.title": "Draws to play — {month} {year}",
    "plan.column.date": "Date",
    "plan.column.day": "Day",
    "plan.column.player": "Player",
    "plan.column.lottery": "Lottery",
    "plan.column.numbers": "Numbers",
    "plan.column.cost": "Cost",
    "plan.column.weight": "Weight",
    "plan.column.allocated": "Allocated",
    "plan.column.committed": "Committed",
    "plan.column.grids": "Grids",
    "plan.column.unused": "Unused",
    "plan.column.unspent": "Unspent",
    "plan.column.budget": "Budget",
    "plan.column.plays": "Plays",
    "plan.column.ceiling": "Ceiling",
    "plan.summary.title": "Budget allocation",
    "plan.players.title": "Per player",
    "plan.totals.title": "Totals",
    "plan.totals.household": "Household totals",
    "plan.empty": "No draw could be planned with this budget.",
    "plan.plays.nothing": "nothing this month",
    "plan.disclaimer": (
        "Draws are independent events. These numbers are not predictions, "
        "and no combination is more likely than another."
    ),
    "plan.ceiling": "Monthly ceiling: ",
    "plan.exported": "Exported to {path}",
    "plan.already.drawn": (
        "Plan already drawn on {date}. Showing it again — pass --force to draw a new one."
    ),
    "plan.replacing": "Replacing the plan drawn on {date}",
    "plan.replacing.warning": (
        "Redrawing until the numbers look right is the bias this tool removes."
    ),
    "plan.player.line": "{name} — ceiling {ceiling}, plays {lotteries}",
    "plan.player.nothing": "nothing",
    # Notes
    "note.shared": "Shared draws",
    "note.shared.body": (
        "{count} draw(s) are played by more than one person: {listed}. "
        "Sharing a draw costs nothing in odds."
    ),
    "note.no.draw": "no draw left in this period",
    "note.unplayed": "only {available} draw(s) left in the period, {unplayed} affordable "
    "grid(s) unplayed",
    "note.below.price": "share of {share} is below the {price} grid price, skipped this month",
    "note.disabled": "disabled (weight is 0)",
    # Config and players
    "config.file": "File",
    "config.ceiling": "Monthly ceiling",
    "config.export": "Export path",
    "config.filters": "Filters",
    "config.lotteries": "Lotteries",
    "config.players": "Players",
    "config.language": "Language",
    "config.plan": "Current plan",
    "config.plan.none": "none drawn yet",
    "config.plan.unreadable": "unreadable",
    "config.plan.drawn": "{month} {year}, drawn {date}",
    "config.saved": "Saved {path}",
    "config.wrote": "Wrote {path}",
    "config.review": "Review the prices and draw days before playing.",
    "config.none": "none",
    "player.saved": "Saved {name} to {path}",
    "player.removed": "Removed {name} from {path}",
    "player.updating": "Updating {name}.",
    "player.none": "No players configured — 'generate' plans for one person.",
    "player.add.hint": "Add someone with 'blindgrid player add'.",
    "player.second.hint": "Add a second person and 'generate' will plan for the household.",
    "player.weight.explain": (
        "Weights are relative shares of that person's budget, not draw counts."
    ),
    "player.weight.example": "Equal weights split it evenly; 0.5 means half as much as a 1.0.",
    "lottery.saved": "Saved {label} to {path}",
    # Errors
    "error.config.missing": (
        "No configuration found at {path}.\nRun 'blindgrid config init' to create one."
    ),
    "error.no.tty": (
        "This step needs an interactive terminal. Pass the values as options "
        "instead, for example: blindgrid generate --budget 30 --lottery Loto"
    ),
    "error.prefix": "Error: ",
    "error.cancelled": "Cancelled.",
    "error.budget.invalid": "{who}{value} is not a valid amount",
    "error.budget.zero": "{who}budget must be greater than zero.",
    "error.budget.ceiling": (
        "{who}budget of {amount} exceeds the configured ceiling of {ceiling}. "
        "Raise max_monthly_budget in your config if this is a considered decision."
    ),
    "error.month": "{value} is not a valid month. Expected YYYY-MM, for example 2026-08.",
    "error.lottery.unknown": "Unknown lottery {label}. Configured: {known}",
    "error.player.unknown": "Unknown player {name}. Configured: {known}",
    "error.no.lottery": "No lottery with a non-zero weight is configured.",
    "error.none.selected": "No lottery selected.",
    "error.nobody": "Nobody is playing this month.",
    "error.budget.format": (
        "With players configured, --budget takes NAME=AMOUNT, for example --budget "
        "'{example}=30'. Got {value}."
    ),
    "error.lottery.solo": (
        "--lottery applies to solo mode. With players configured, each person's "
        "lotteries come from their own weights."
    ),
    "error.player.solo": (
        "--player needs players in your config. Add one with 'blindgrid player add'."
    ),
    "error.exists": "{path} already exists. Pass --force to overwrite it.",
    "error.name.empty": "A player needs a name.",
    "error.plays.nothing": "Someone who plays nothing has nothing to plan.",
    "error.no.lotteries": "Add a lottery first with 'blindgrid lottery add'.",
    "error.not.number": "{value} is not a number",
    "error.weight.positive": "Weight for {label} must be greater than zero, or leave it unchecked.",
    "error.plan.ignored": "Ignoring the saved plan: {reason}",
    "error.plan.unsaved": "Could not save this plan, it will not be remembered: {reason}",
    "error.language": "Unknown language {value}. Available: {known}",
    # Months
    "month.1": "January",
    "month.2": "February",
    "month.3": "March",
    "month.4": "April",
    "month.5": "May",
    "month.6": "June",
    "month.7": "July",
    "month.8": "August",
    "month.9": "September",
    "month.10": "October",
    "month.11": "November",
    "month.12": "December",
    # Weekdays, Monday first
    "weekday.0": "Monday",
    "weekday.1": "Tuesday",
    "weekday.2": "Wednesday",
    "weekday.3": "Thursday",
    "weekday.4": "Friday",
    "weekday.5": "Saturday",
    "weekday.6": "Sunday",
}
