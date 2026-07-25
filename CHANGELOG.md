# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

- A month is now drawn once. `generate` saves the plan to
  `~/.local/state/blindgrid/plan.json` and shows it again on later runs, so it
  can be found while the grids are being filled in. `--force` draws a new one
  and states what it replaces.
- `config show` reports where the current plan lives and when it was drawn.

### Changed

- The stored plan is one file, replaced when the month turns, and a
  self-contained snapshot: editing the configuration afterwards does not alter
  a plan already drawn. This narrows the original "no persistence" rule to
  what it was protecting against — an accumulated history of past grids, which
  is still out of scope — while removing the ability to reroll a month until
  the numbers look right.

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

[Unreleased]: https://github.com/adrnbttr/blindgrid/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/adrnbttr/blindgrid/releases/tag/v0.1.0
