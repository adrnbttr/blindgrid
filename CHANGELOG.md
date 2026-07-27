# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2026-07-27

### Added

- **Households.** Declare people with `blindgrid player add`, or `[[player]]`
  blocks in the config, and `generate` plans for everyone in one pass. Each
  person keeps their own ceiling and their own lotteries, with their own
  weights; nobody's budget affects anyone else's share, and there is
  deliberately no household cap.
- Draws are spread across dates so the same lottery is not played twice on the
  same day while free dates remain. This does **not** improve anyone's odds —
  two grids are two independent chances either way — and the documentation
  says so plainly. When dates run short they are shared rather than grids
  dropped, and the output reports it.
- `player add`, `player list` and `player remove`.
- **Windows support.** `install.ps1` mirrors the Unix installer, and
  configuration and state follow `%APPDATA%` / `%LOCALAPPDATA%` on Windows
  while keeping XDG elsewhere. CI now runs the test suite on Linux, macOS and
  Windows, and exercises both installers end to end on each.
- Past draws are struck through when a plan is shown again, so what is left to
  play stands out.
- **Translations.** The interface is available in English, French, Spanish and
  German, chosen with `--lang`, `BLINDGRID_LANG`, the config file or your
  system locale. Tests enforce that every catalogue matches the English one
  key for key and placeholder for placeholder.
- A month is now drawn once. `generate` saves the plan to the state directory
  and shows it again on later runs, so it can be found while the grids are
  being filled in. `--force` draws a new one and states what it replaces.
- `config show` reports where the current plan lives and when it was drawn.
- **Runs on an iPad.** `install.py` installs anywhere Python exists, which is
  what iOS needs: a-Shell has neither bash nor git, so it pulls a source
  archive rather than a git URL. `python -m blindgrid` works where a
  pip-installed command does not reach the PATH.
- The plan lays itself out for narrow terminals. Below the width the table
  needs, each draw becomes two lines with its numbers unwrapped on their own —
  at 60 columns the table used to stack them one digit per line and cut the
  lottery name to `Eur…`. `--compact` and `--table` force either layout.

### Changed

- Number columns line up across the whole plan. Lotteries of different shapes
  used to leave the separator and pool names drifting from row to row, which
  is exactly the wrong thing when numbers are being copied onto a slip.
  Weights share one precision so their decimal points align.
- Amounts accept the way people type them: `30 €`, `30€`, `30 EUR`, commas and
  non-breaking spaces. Nonsense is still refused.
- `--lang` is accepted before the command as well as after it.
- The stored plan is one file, replaced when the month turns, and a
  self-contained snapshot: editing the configuration afterwards does not alter
  a plan already drawn. This narrows the original "no persistence" rule to
  what it was protecting against — an accumulated history of past grids, which
  is still out of scope — while removing the ability to reroll a month until
  the numbers look right.

### Fixed

- Asked to prompt with no terminal attached — a pipe, a cron job, one of the
  iOS shells — the tool now says which option to use instead, rather than
  raising a bare `OSError` from inside prompt_toolkit.
- The help screen no longer mixed languages: Typer takes a command's docstring
  as its help text unless told otherwise, which left the top-level commands in
  English while the sub-apps were translated.
- The message shown when no configuration exists yet — the first thing a new
  user sees — is translated.
- A language given before the command is no longer overwritten when the
  configuration is read.

## [0.1.0] - 2026-07-25

First public release.

### Added

- `generate` — interactive monthly planning: prompts for a budget and a set of
  lotteries, allocates the money by weight, picks draw dates at random and
  produces one grid per selected draw.
- Weighted budget allocation with a hard ceiling that has no override. Shares
  round down, leftovers stay unspent, and a share too small for one grid skips
  that lottery with an explicit note rather than borrowing from another.
- Draw planner enumerating real calendar dates, capped by the draws actually
  remaining in the period.
- Grid generation from `secrets.SystemRandom` with rejection sampling against
  five anti-pattern filters, each expressed relative to pool size and each
  switching itself off on pools too small to satisfy it.
- `rich` table output and a Markdown export, overwritten on every run.
- `config init` / `config show` / `config edit` and `lottery add` /
  `lottery list`.
- TOML configuration describing lotteries generically: any game in any country
  is a matter of price, draw days and pools of numbers.
- Test suite covering allocation, planning, filters, generation, config and
  the CLI, including a contract test asserting that `random` is never imported
  by the package.

[Unreleased]: https://github.com/adrnbttr/blindgrid/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/adrnbttr/blindgrid/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/adrnbttr/blindgrid/releases/tag/v0.1.0
