# Installation guide

blindgrid runs on Linux, macOS, Windows, and on an iPad or iPhone. The short
version:

**macOS and Linux**

```bash
curl -fsSL https://raw.githubusercontent.com/adrnbttr/blindgrid/main/install.sh | bash
```

**Windows** (PowerShell)

```powershell
irm https://raw.githubusercontent.com/adrnbttr/blindgrid/main/install.ps1 | iex
```

**iPad and iPhone**, inside [a-Shell](https://holzschu.github.io/a-Shell_iOS/)

```bash
curl -sL https://raw.githubusercontent.com/adrnbttr/blindgrid/main/install.py | python3
```

The rest of this page is for when that is not what you want, or when it does
not go to plan.

## On an iPad or iPhone

### Which terminal

**[a-Shell](https://holzschu.github.io/a-Shell_iOS/)** — free, on the App
Store, and the one this is tested against. It ships its own Python and pip, so
nothing has to be compiled and nothing has to be jailbroken. Install it, open
it, and paste the command above.

Two things it does not have, which is why there is a third installer:

- **no bash**, so `install.sh` cannot run — `install.py` needs only Python;
- **no git**, so `pip install git+…` fails — the installer pulls a source
  archive instead.

Alternatives, if you would rather not use a-Shell:

| | Verdict |
| --- | --- |
| **iSH** | Works. Emulates x86 Alpine, so it is noticeably slower, and you install Python yourself with `apk add python3`. |
| **Blink Shell** or **Termius** | Best of all, but as SSH clients: the tool runs on a machine elsewhere and your iPad is the screen. Nothing to install on the device. |
| **Pythonista**, **Pyto** | Python IDEs rather than shells. A command-line tool with subcommands is awkward there. |

### Running it

a-Shell does not always put a pip-installed command on the `PATH`, so use the
module form:

```bash
python3 -m blindgrid generate
python3 -m blindgrid config show
```

### Prompts

If your shell cannot draw interactive prompts, pass the values as options —
every prompt has one, and the tool then needs no terminal at all:

```bash
python3 -m blindgrid generate --budget 30 --lottery Loto
python3 -m blindgrid generate --budget "Adrien=20" --budget "Marie=12"
```

Asked for something it cannot prompt for, blindgrid says so and shows the
option to use instead, rather than failing with a traceback.

### The screen

An iPad in portrait gives you around 60 columns, which is not enough for the
table. blindgrid measures and switches to a list where each draw's numbers sit
on their own line, unwrapped and untruncated — see
[On a tablet or a phone](../README.md#on-a-tablet-or-a-phone). Rotating to
landscape brings the table back. `--compact` and `--table` override the
choice.

### Where your files go

a-Shell sandboxes each app, so everything lands inside its own container —
`~/Documents/` is the part you can reach from the Files app. `blindgrid config
show` prints the exact paths. Worth knowing: **uninstalling a-Shell deletes
your configuration with it**, so if your budget ceiling matters to you, keep a
copy of `config.toml` somewhere in iCloud.

## What the installer does

It installs into your own user profile and nowhere else. Specifically:

1. Looks for `uv`, then `pipx`, then a Python 3.11 or newer.
2. Installs blindgrid with the first of those it finds.
3. Writes a starter config, unless one is already there.
4. Tells you whether the install directory is on your `PATH`, and exactly what
   to add if it is not.

It never runs `sudo` or asks for administrator rights, never writes outside
your home directory, and never installs a third-party tool behind your back —
if neither uv nor pipx is present, it falls back to a plain virtual
environment built with the Python you already have.

There are three, one per world: `install.sh` for macOS and Linux,
`install.ps1` for Windows, and `install.py` wherever only Python exists —
which is what makes iOS possible, since a-Shell has neither bash nor git.

All three are exercised on every push: CI installs the project with them on
clean Linux, macOS and Windows runners, runs the installed command, and
uninstalls again. The Python one is additionally checked at 55 columns, and
with no terminal attached, since that is what an iPad looks like.

### Reading it before running it

Piping a script from the internet into a shell means trusting whoever controls
that URL. If you would rather look first:

```bash
curl -fsSLO https://raw.githubusercontent.com/adrnbttr/blindgrid/main/install.sh
less install.sh
bash install.sh
```

```powershell
irm https://raw.githubusercontent.com/adrnbttr/blindgrid/main/install.ps1 -OutFile install.ps1
notepad install.ps1
.\install.ps1
```

Each is a few hundred lines, linted in CI by shellcheck and PSScriptAnalyzer
respectively.

### Options

| Unix | Windows | Python | Effect |
| --- | --- | --- | --- |
| `--method uv\|pipx\|venv` | `-Method Uv\|Pipx\|Venv` | — | Force an install method instead of auto-detecting. |
| `--source <path\|url>` | `-Source <path\|url>` | `--source` | Install from somewhere else — a local clone, a fork. |
| `--ref <branch\|tag>` | `-Ref <branch\|tag>` | `--ref` | Install a specific version. Default `main`. |
| `--no-config` | `-NoConfig` | `--no-config` | Do not create a starter configuration. |
| `--uninstall` | `-Uninstall` | — | Remove blindgrid, keeping your configuration. |
| — | — | `--check` | Report what would happen, install nothing. |
| `--help` | `Get-Help .\install.ps1` | `--help` | Show the options. |

The Python installer has no `--uninstall`: it installs with pip, so pip
removes it — `python3 -m pip uninstall blindgrid`.

Environment: on Unix, `BLINDGRID_PREFIX` changes the install prefix (default
`~/.local`). `NO_COLOR` turns off colour on both.

### If PowerShell refuses to run the script

Windows blocks downloaded scripts by default. Allow signed-and-local scripts
for your own user, which does not require administrator rights:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

The `irm … | iex` form above is not affected, since nothing touches disk.

## Where files live

Two directories, kept apart on purpose: your configuration is yours to edit
and is never deleted by an uninstall, while the current plan is
machine-written and regenerable.

| | Configuration | Current plan |
| --- | --- | --- |
| **Linux** | `~/.config/blindgrid/` | `~/.local/state/blindgrid/` |
| **macOS** | `~/.config/blindgrid/` | `~/.local/state/blindgrid/` |
| **Windows** | `%APPDATA%\blindgrid\` | `%LOCALAPPDATA%\blindgrid\` |
| **iOS** | inside the shell app's own sandbox | same |

Linux and macOS follow the XDG base directory spec. macOS uses `~/.config`
rather than `~/Library/Application Support` because this is a terminal tool
whose configuration you are expected to open in an editor, and `~/.config` is
where that is looked for. Windows splits roaming (`%APPDATA%`, follows you
between machines) from local (`%LOCALAPPDATA%`, does not) — a config worth
carrying, a plan that is not.

Override either with `BLINDGRID_CONFIG` and `BLINDGRID_STATE`. A `config.toml`
in the current directory always wins, which is how you keep a separate setup
per folder.

`blindgrid config show` prints exactly what is in effect.

## Installing without the script

All three are equivalent. Pick whichever tool you already use.

**uv** — fastest, and brings its own Python if you have none:

```bash
uv tool install git+https://github.com/adrnbttr/blindgrid.git
```

**pipx** — the classic choice for Python CLIs:

```bash
pipx install git+https://github.com/adrnbttr/blindgrid.git
```

**A virtualenv you manage yourself:**

```bash
python3 -m venv ~/.local/share/blindgrid/venv
~/.local/share/blindgrid/venv/bin/pip install git+https://github.com/adrnbttr/blindgrid.git
ln -s ~/.local/share/blindgrid/venv/bin/blindgrid ~/.local/bin/blindgrid
```

**From a clone, for development** — see [CONTRIBUTING.md](../CONTRIBUTING.md).

## Requirements

- **Python 3.11 or newer.** Only for the venv and pipx routes; uv downloads its
  own interpreter if yours is older.
- **A terminal that renders UTF-8.** The tables use box-drawing characters.
  Windows Terminal, iTerm2, and anything on Linux from the last decade are
  fine. The old `cmd.exe` console will mangle them — use Windows Terminal,
  which ships with Windows 11 and is a free install on Windows 10.
- No database, no network access at runtime, no account. The tool reads a TOML
  file and writes a Markdown one.

If your system Python is too old:

```bash
brew install python@3.12                       # macOS
sudo apt install python3.12 python3.12-venv    # Debian, Ubuntu
```

```powershell
winget install Python.Python.3.12              # Windows
```

## After installing

```bash
blindgrid config show     # where is my config, what is in it
blindgrid generate        # plan this month
```

`generate` plans the current month, so there is nothing to pass on the first of
the month. Run it again later and it shows you the same plan rather than
drawing a new one — see [A month is drawn once](../README.md#a-month-is-drawn-once).

**Open your config before you play.** The shipped example carries three French
games with prices checked in July 2026, and a `max_monthly_budget` of 40. Both
are illustrations, not recommendations:

```bash
blindgrid config edit     # guided, or just open the file
```

The ceiling is the number that matters. `generate` refuses any budget above it
and there is no override flag, so pick it now rather than in front of a
jackpot headline.

## Language

The interface is available in English, French, Spanish and German, and follows
your system locale by default:

```bash
blindgrid generate --lang fr     # this run only
blindgrid config edit            # choose one and keep it
export BLINDGRID_LANG=de         # for a shell session
```

Precedence: `--lang`, `BLINDGRID_LANG`, the `language` key in your config file,
your system locale, then English.

## Troubleshooting

### `blindgrid: command not found`

The install directory is not on your `PATH`. The installer prints the exact
line to add. On macOS and Linux it is usually:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

Put that in `~/.zshrc` (zsh, the default on macOS) or `~/.bashrc`, then open a
new terminal. With uv you can also run `uv tool update-shell`.

On Windows, set it for your user and open a new terminal:

```powershell
[Environment]::SetEnvironmentVariable('PATH', "$env:PATH;$env:LOCALAPPDATA\Programs\blindgrid", 'User')
```

### `No configuration found at ...`

Nothing has created a config yet:

```bash
blindgrid config init
```

blindgrid looks for one in this order: `$BLINDGRID_CONFIG`, then `config.toml`
in the current directory, then the per-platform location in
[where files live](#where-files-live). The current-directory rule means you
can keep a separate setup per folder without touching the global one.

### `error: externally-managed-environment`

Your system Python refuses direct `pip install`, which is correct of it. Use
uv or pipx, or the installer, which handles this for you. Do not pass
`--break-system-packages`.

### The tables look like mojibake

On macOS or Linux, your terminal is not in a UTF-8 locale:

```bash
export LANG=en_US.UTF-8
```

On Windows, the classic `cmd.exe` console still defaults to a legacy code
page. Use Windows Terminal, or force UTF-8 in the current session:

```powershell
chcp 65001
$env:PYTHONIOENCODING = 'utf-8'
```

### `running scripts is disabled on this system`

PowerShell's execution policy is blocking `install.ps1`. Allow it for your own
user — no administrator rights needed:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

### Something else

Open an issue with the output of `blindgrid config show` and your Python
version: <https://github.com/adrnbttr/blindgrid/issues>

## Updating

Re-run the installer. It replaces the installed version and leaves your
configuration alone:

```bash
curl -fsSL https://raw.githubusercontent.com/adrnbttr/blindgrid/main/install.sh | bash
```

```powershell
irm https://raw.githubusercontent.com/adrnbttr/blindgrid/main/install.ps1 | iex
```

Or `uv tool upgrade blindgrid` / `pipx upgrade blindgrid`.

## Uninstalling

From a clone:

```bash
bash install.sh --uninstall
```

```powershell
.\install.ps1 -Uninstall
```

Or without one, passing the flag through:

```bash
curl -fsSL https://raw.githubusercontent.com/adrnbttr/blindgrid/main/install.sh | bash -s -- --uninstall
```

```powershell
& ([scriptblock]::Create((irm https://raw.githubusercontent.com/adrnbttr/blindgrid/main/install.ps1))) -Uninstall
```

Your configuration and current plan are deliberately left behind. Remove them
yourself:

```bash
rm -rf ~/.config/blindgrid ~/.local/state/blindgrid
```

```powershell
Remove-Item -Recurse -Force "$env:APPDATA\blindgrid", "$env:LOCALAPPDATA\blindgrid"
```
