# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
