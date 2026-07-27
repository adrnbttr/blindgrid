<div align="center">

<img src="https://raw.githubusercontent.com/adrnbttr/blindgrid/main/docs/logo.svg" alt="" width="88" height="88">

<h1>blindgrid</h1>

<p>
  <b>Lottery grids from cryptographic randomness,<br>
  inside a budget you cannot exceed.</b>
</p>

<p>
  <a href="https://github.com/adrnbttr/blindgrid/actions/workflows/ci.yml"><img src="https://github.com/adrnbttr/blindgrid/actions/workflows/ci.yml/badge.svg" alt="CI status"></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.11%2B-blue" alt="Python 3.11+"></a>
  <a href="https://github.com/adrnbttr/blindgrid/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-green" alt="MIT license"></a>
  <img src="https://img.shields.io/badge/predictions-none-lightgrey" alt="Predictions: none">
</p>

<p>
  <a href="#install">Install</a> ·
  <a href="#what-this-is-not">What it refuses to do</a> ·
  <a href="#playing-as-a-household">Households</a> ·
  <a href="#on-a-tablet-or-a-phone">Tablets</a> ·
  <a href="#language">Language</a> ·
  <a href="#adding-a-lottery-from-any-country">Add your own lottery</a> ·
  <a href="#responsible-gambling">Responsible gambling</a>
</p>

<img src="https://raw.githubusercontent.com/adrnbttr/blindgrid/main/docs/demo.gif" alt="blindgrid prompting for a budget, then printing a month of draws" width="880">

</div>

## What this is

A small CLI that answers two questions once a month:

- **Which draws should I play?** Given a budget and a set of lotteries, it
  allocates the money by weight, picks real calendar dates at random, and
  stops. No pattern, no habit, no "I always play on Saturdays".
- **Which numbers?** Drawn from `secrets.SystemRandom`, then filtered against a
  handful of anti-pattern rules so the grid does not look like something a
  human would have chosen.

The plan is printed as a table and exported to a Markdown file.

## What this is not

**It does not predict anything, and it never will.** Lottery draws are
independent events. The numbers drawn last week carry no information about next
week's draw; a number that has not come up in two years is not "due". This is
not an opinion about lotteries, it is what independence means.

So the following are permanently out of scope, and pull requests adding them
will be declined:

| Not here | Why |
| --- | --- |
| Historical draw data, frequency statistics, hot/cold numbers | Past draws say nothing about future ones. Displaying them implies otherwise. |
| A `--seed` flag or any deterministic mode | Reproducible numbers reintroduce exactly the structure this tool removes. |
| A history of past months | Months of stored grids invite comparing them against results, and comparing invites pattern-hunting. The current month is kept so you can find it again — one file, replaced, never accumulated. |
| Any attempt to spend the budget exactly | Unspent money is a good outcome. A tool that consumed the envelope would encourage spending. |

What is left, then? Two honest things: **randomness without human bias**, and a
**budget ceiling that does not move**.

### Why filter the numbers at all, if every combination is equally likely?

Because the *payout* is not equally likely. Every combination has the same
probability of being drawn, but combinations humans favour — birthdates below
32, sequences, neat patterns — are picked by thousands of other players at the
same time. When such a combination wins, the jackpot is split. Filtering does
not improve your odds of winning; it improves what you would receive if you
did.

The rule set stays deliberately small for the same reason. Every additional
rule shrinks the sample space, and a heavily filtered "random" pick is just a
different kind of predictable.

## Install

Runs on Linux, macOS, Windows, and iOS through a-Shell.

```bash
pip install blindgrid        # or: uv tool install blindgrid
```

That is the whole of it if you already have Python 3.11 or newer. The scripts
below add a little more: they pick an install method for you, write a starter
configuration, and tell you what to put on your `PATH`.

**macOS and Linux**

```bash
curl -fsSL https://raw.githubusercontent.com/adrnbttr/blindgrid/main/install.sh | bash
```

**Windows** (PowerShell)

```powershell
irm https://raw.githubusercontent.com/adrnbttr/blindgrid/main/install.ps1 | iex
```

Either one installs into your own user profile, writes a starter config, and
tells you what to add to your `PATH` if anything is missing. Neither asks for
`sudo` or administrator rights, and neither writes outside your home
directory. Prefer to read the script first? Download it and open it — both are
short, and both are linted in CI (shellcheck, PSScriptAnalyzer).

Python 3.11 or newer is required, except with uv, which brings its own.
**3.11 is a floor, not a default**: it is the newest Python a-Shell ships, and
raising it would drop iPad support — a test says so.
Uninstalling is `install.sh --uninstall` / `install.ps1 -Uninstall`, and your
config survives it.

**iPad and iPhone**, in [a-Shell](https://holzschu.github.io/a-Shell_iOS/)
(free, App Store):

```bash
pip install blindgrid
```

Then `python3 -m blindgrid generate`. Every dependency is pure Python, which is
what makes this work on a device with no compiler. If pip is not on your path
there, `curl -sL https://raw.githubusercontent.com/adrnbttr/blindgrid/main/install.py | python3`
does the same and sets up a starter config — see
[On a tablet or a phone](#on-a-tablet-or-a-phone).

**[Full installation guide](https://github.com/adrnbttr/blindgrid/blob/main/docs/installation.md)** — per-platform details,
other install methods, file locations, troubleshooting, updating, uninstalling.

## Use

```bash
blindgrid config show      # where your config lives and what is in it
blindgrid generate         # plan the current month
```

`generate` asks for two things — the budget for this month, and which lotteries
to include — then prints the plan and writes `plan.md`. It plans the current
month by default; `--month` is only there for planning ahead.

### A month is drawn once

Run `generate` again and you get the same plan back, not a new one:

```
$ blindgrid generate
Plan already drawn on 2026-09-01. Showing it again — pass --force to draw a new one.
```

This is partly convenience — you can come back to it while you fill your grids
— but mostly it is the point. A tool that redrew on every run would let you
reroll until the numbers looked right, and picking the draw you like best is
exactly the bias the filters exist to remove.

`--force` is there for the genuine mistake, a mistyped budget or the wrong
lotteries. It says what it is replacing before it does it.

The plan lives in one file in your state directory (see
[file locations](https://github.com/adrnbttr/blindgrid/blob/main/docs/installation.md#where-files-live)), replaced when the
month turns. It is a self-contained snapshot, so editing your config
afterwards never changes a plan you already hold. Draws whose date has passed
are struck through when the plan is shown again, so what is left to play is
obvious.

## On a tablet or a phone

The plan lays itself out to fit. Below roughly 80 columns — an iPad in
portrait, a phone, a split view — the table is dropped for a list, and the
numbers get a line to themselves:

```
September 2026

 8 Tue  EuroMillions  Adrien  2.50 EUR
    10 11 30 34 47  ·  stars  8 12

 9 Wed  Loto  Adrien  2.20 EUR
     7 20 22 34 35  ·  lucky  2
```

The numbers are the one thing you copy onto a paper slip, so they are never
wrapped and nothing is ever cut to `Eur…`. It stays readable down to about 40
columns. `--compact` and `--table` force either layout.

## Playing as a household

Two people, one month, one command. Everyone keeps their own ceiling and their
own games:

```bash
blindgrid player add     # name, ceiling, which lotteries, what weights
blindgrid generate       # asks each person for their budget, then plans
```

```
╭────────────┬───────────┬────────┬──────────────┬──────────────────────────┬──────────╮
│ Date       │ Day       │ Player │ Lottery      │ Numbers                  │     Cost │
├────────────┼───────────┼────────┼──────────────┼──────────────────────────┼──────────┤
│ 2026-09-11 │ Friday    │ Adrien │ EuroMillions │ 10 11 22 35 36 · stars…  │ 2.50 EUR │
│ 2026-09-19 │ Saturday  │ Marie  │ Loto         │  4  5 10 38 42 · lucky 3 │ 2.20 EUR │
│ 2026-09-21 │ Monday    │ Marie  │ EuroDreams   │  7  9 18 32 34 · dream 5 │ 2.50 EUR │
╰────────────┴───────────┴────────┴──────────────┴──────────────────────────┴──────────╯
```

Three things hold:

- **Nobody spends against anyone else's ceiling.** Each person has their own
  `max_monthly_budget`, and one player's budget never changes another's share.
  There is no household cap, on purpose: if two people together want to spend
  more than they should, that is a conversation, not something software gets
  to arbitrate.
- **Everyone plays only their own games.** Weights are per person; a weight of
  zero, or simply leaving a lottery out, means they never play it.
- **Draws are spread out.** The household covers as many different draws as it
  can before any date is played twice.

### On spreading draws

Spreading **does not improve anyone's odds**, and the tool will never claim it
does. Two grids are two independent chances whether they sit on the same draw
or on two different ones, and the probability that at least one of them wins
is identical either way.

What it does buy is exposure to more distinct jackpots — some of which have
rolled over and are larger — and the certainty that two people in one house
are not holding near-duplicate tickets for a single draw. That is
diversification, not an edge.

When there are fewer draws left than grids to play, dates are shared rather
than grids dropped, and the output says which. Losing a grid someone budgeted
for, to satisfy a rule that does not change the odds, would be the wrong
trade.

```toml
[[player]]
name = "Adrien"
max_monthly_budget = 40.00
  [player.weight]
  EuroMillions = 1.0
  Loto = 1.0
  EuroDreams = 0.4

[[player]]
name = "Marie"
max_monthly_budget = 25.00
  [player.weight]
  Loto = 1.0
  EuroDreams = 1.0
```

Declare nobody and blindgrid stays in single-player mode, exactly as before.

```
Usage: blindgrid [OPTIONS] COMMAND [ARGS]...

  generate    Build this month's plan: how much to spend, which draws, which numbers.
  config      Inspect and edit the configuration.
  lottery     Manage lottery definitions.
  player      Manage the people who play.
  version     Print the installed version.
```

Useful options on `generate`:

| Option | Effect |
| --- | --- |
| `-b, --budget 30` | Skip the prompt and use this amount. With players: `-b "Adrien=30"`, repeatable. |
| `-l, --lottery Loto` | Include a specific lottery. Repeatable. Single-player mode only. |
| `-p, --player Marie` | Limit the plan to these people. Repeatable. |
| `-m, --month 2026-09` | Plan a month other than the current one. |
| `--force` | Draw a new plan even though this month already has one. |
| `--no-export` | Print the plan without writing `plan.md`. |
| `--lang fr` | Interface language for this run. See [Language](#language). |
| `--compact` / `--table` | Force the narrow layout, or the table. Default: whichever fits. |
| `-c, --config path` | Use a specific configuration file. |

Every prompt has an option that skips it, so the whole tool works without an
interactive terminal — in a script, over SSH, or in a shell that cannot draw
prompts.

## Language

The interface speaks **English, French, Spanish and German**. It follows your
system locale by default, so there is usually nothing to set:

```bash
blindgrid generate --lang fr     # just this run
blindgrid config edit            # pick one and keep it
export BLINDGRID_LANG=es         # for a shell session
```

Order of precedence: `--lang`, then `BLINDGRID_LANG`, then `language` in the
config file, then your system locale, then English.

Only the interface is translated. Lottery labels, pool names and player names
are printed exactly as you wrote them, and the weekday keys in the config file
stay English (`monday`, `tuesday`, …) — those are a file format, not text for
reading.

Adding a language is one file in `src/blindgrid/i18n/` plus one line in its
`__init__.py`. Tests check that every catalogue carries exactly the same keys
and placeholders as the English one, so a half-finished translation fails the
build rather than leaking English sentences into someone's session.

## Configuration

Two files:

- `config.example.toml` — versioned, three French games as an illustration.
- `config.toml` — yours, gitignored, holding your own ceiling.

The ceiling is the point of the file:

```toml
max_monthly_budget = 40.00
```

`generate` refuses any budget above it. There is no override flag. A cap you
can raise in the moment while looking at a jackpot headline is not a cap.

### Adding a lottery from any country

Nothing in the code knows about France, or about any specific game. A lottery
is a price, a set of draw days, and one or more pools of numbers. That is the
whole model, and it covers every draw-style lottery I am aware of.

Here is the US **Powerball** — five numbers from 69, plus one from 26, drawn on
Mondays, Wednesdays and Saturdays at $2 a play:

```toml
[[lottery]]
label = "Powerball"
currency = "USD"
price_per_grid = 2.00
draw_days = ["monday", "wednesday", "saturday"]
weight = 1.0

  [[lottery.pool]]
  name = "numbers"
  count = 5
  max = 69

  [[lottery.pool]]
  name = "powerball"
  count = 1
  max = 26
```

Drop that into `config.toml` and it works. Or run `blindgrid lottery add` and
answer the prompts.

The filters adapt on their own: the 1-from-26 Powerball pool is too small for a
parity or spread rule to mean anything, so those rules switch themselves off
for it rather than searching forever for a combination that cannot exist.

### Weights

Weights are relative shares of one envelope, not draw counts.

```toml
weight = 1.0   # EuroMillions
weight = 1.0   # Loto
weight = 0.4   # EuroDreams — played, but a smaller slice
weight = 0.0   # disabled, without deleting the definition
```

With a €40 budget and those weights, EuroMillions and Loto receive €16.66 each
and EuroDreams €6.66. Each share then buys as many grids as it can afford, and
**the leftover in each share stays unspent**. It is never pooled, never
redistributed, never rounded up into one more grid.

If a share cannot cover a single grid, that lottery is skipped for the month
and the output says so explicitly. It never borrows from another share to make
itself viable.

## The randomness

Every number comes from `secrets.SystemRandom`, which draws from the operating
system's entropy pool. The `random` module is not imported anywhere in the
package — its Mersenne Twister is seedable and reproducible, which is a
liability here — and a test enforces that.

The same source picks which dates to play, because a schedule chosen by habit
is as predictable as numbers chosen by birthdate.

## Development

```bash
uv pip install -e ".[dev]"
pytest
ruff check .
ruff format --check .
```

CI runs both on Python 3.11, 3.12 and 3.13.

## Responsible gambling

This tool exists because a budget written down and capped is better than a
budget decided in the moment. It does not make gambling profitable. Over any
meaningful number of draws, the expected return of a lottery ticket is
negative — that is how lotteries fund themselves — and no arrangement of
numbers changes that.

Play with money you have already decided to lose. If gambling has stopped being
a small monthly cost and started being something else, these services are free
and confidential:

- **France** — Joueurs Info Service, 09 74 75 13 13, <https://www.joueurs-info-service.fr>
- **United Kingdom** — GamCare, 0808 8020 133, <https://www.gamcare.org.uk>
- **United States** — 1-800-GAMBLER, <https://www.ncpgambling.org>
- **International** — <https://www.gamblingtherapy.org>

## License

MIT — see [LICENSE](https://github.com/adrnbttr/blindgrid/blob/main/LICENSE).
