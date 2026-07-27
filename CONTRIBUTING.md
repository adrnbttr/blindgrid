# Contributing

Thanks for taking a look. This is a small project with a narrow purpose, so
the most useful thing to read first is the section below on what will not be
merged — it is not a long list, but it is a firm one.

## Out of scope, permanently

The README explains the reasoning; this is the short version.

- **Anything predictive.** Frequency analysis, hot/cold numbers, historical
  draw data, "due" numbers, statistical models of past results. Lottery draws
  are independent events. A feature that implies otherwise is a bug in the
  product, not a missing capability.
- **Seeding or reproducible output.** No `--seed`, no deterministic mode, no
  fixed generator in the package. A test enforces this.
- **A history of past months.** The current plan is kept in one file so it can
  be found again, and replaced when the month turns. Accumulating months is a
  different thing: it makes past grids comparable to results, which is where
  pattern-hunting starts.
- **Consuming the budget exactly.** Leftover money stays unspent.
- **Hardcoding a country or a game.** Lotteries live in configuration. If
  something cannot be expressed as a price, a set of draw days and pools of
  numbers, open an issue and let's discuss the model rather than special-case
  the code.
- **Claiming that spreading a household's draws improves anyone's odds.** It
  does not. Two grids are two independent chances whether they sit on one draw
  or two. Spreading buys exposure to more distinct jackpots and avoids
  near-duplicate tickets in one house; the wording in the code and docs says
  exactly that, and should stay that way.

Everything else is fair game: better rendering, clearer errors, more
platforms, faster tests, documentation.

## Setup

```bash
git clone https://github.com/adrnbttr/blindgrid.git
cd blindgrid
uv venv
uv pip install -e ".[dev]"
```

## Before opening a pull request

```bash
ruff check .
ruff format .
pytest
shellcheck install.sh   # only if you touched the Unix installer
```

CI runs the same commands on Linux (3.11, 3.12, 3.13), macOS and Windows, and
a pull request needs them green. It also installs the project with
`install.sh` and `install.ps1` on clean runners and uninstalls them again, so
a change to either is exercised for real rather than merely linted.

If you touched `install.ps1` and have no Windows machine, push and let CI run
PSScriptAnalyzer and the install-uninstall round trip — that is how it is
maintained here. The same goes for `install.py`, which exists for iOS: no CI
runner is an iPad, so it is checked on a bare interpreter, at 55 columns, and
with no terminal attached.

### Platform-specific code

There is exactly one place that branches on the operating system:
`src/blindgrid/paths.py`, which decides where configuration and state live.
Everything else is platform-neutral, and should stay that way. `tests/
test_paths.py` fakes each platform, so both layouts are checked wherever the
suite runs.

## Conventions

- **Commits** follow [Conventional Commits](https://www.conventionalcommits.org):
  `feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `chore:`, `ci:`.
- **Line length** is 100 characters, enforced by ruff.
- **Type annotations** are required on new functions; `ANN` rules are on.
- **Money** is `Decimal`, never `float`. Budget arithmetic in binary floating
  point drifts, and the whole point of the ceiling is that it does not move.
- **Randomness** comes from the `RandomSource` protocol, and production code
  passes `secrets.SystemRandom`. Do not import `random` inside the package.

## Adding an anti-pattern filter

Think twice. Every active rule shrinks the sample space, and a heavily
filtered draw is a predictable draw. If a rule is still worth it:

1. Add the predicate functions and a `Rule` entry in `src/blindgrid/filters.py`.
2. Give it an `applies_to` that switches it off for pools too small to satisfy
   it, expressed relative to `count` and `maximum` — never against a specific
   lottery's numbers.
3. Add it to the `[filters]` block in `config.example.toml`.
4. Cover both the rejection and the degradation in `tests/test_filters.py`.

## Adding a language

One file in `src/blindgrid/i18n/`, copied from `en.py` and translated, plus one
line in that package's `__init__.py` and one entry in `LANGUAGE_NAMES`.

Tests then check that your catalogue carries exactly the English keys, with
exactly the same `{placeholders}`, and that nothing longer than three words was
left in English. A half-finished translation fails the build rather than
leaking English into someone's session.

Translate the interface only. Lottery labels, pool names and player names come
from configuration, and the weekday keys in the config file (`monday`, …) are
a file format rather than text for reading — both stay as they are.

## Regenerating the README image

`docs/demo.gif` is recorded from a real run, not drawn by hand. It needs
[vhs](https://github.com/charmbracelet/vhs):

```bash
brew install vhs        # or see the vhs README for other platforms
vhs docs/demo.tape      # from the repository root
```

The tape points the tool at a throwaway config in a temporary directory, so
recording never touches your own `config.toml`. Regenerate after any change to
`render.py`, and expect different numbers every time — the demo draws from the
real CSPRNG like everything else.

Keep it in English and keep it short. Switching languages mid-recording spends
five seconds saying what one line of the README says better, and every second
is weight on a page people load before deciding whether to read it.
