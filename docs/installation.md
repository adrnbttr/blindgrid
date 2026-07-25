# Installation guide

blindgrid runs on Linux, macOS and Windows. The short version:

**macOS and Linux**

```bash
curl -fsSL https://raw.githubusercontent.com/adrnbttr/blindgrid/main/install.sh | bash
```

**Windows** (PowerShell)

```powershell
irm https://raw.githubusercontent.com/adrnbttr/blindgrid/main/install.ps1 | iex
```

The rest of this page is for when that is not what you want, or when it does
not go to plan.

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

Both scripts are exercised on every push: CI installs the project with them on
a clean Linux, macOS and Windows runner, runs the installed command, then
uninstalls and checks that the configuration survived.

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

| Unix | Windows | Effect |
| --- | --- | --- |
| `--method uv\|pipx\|venv` | `-Method Uv\|Pipx\|Venv` | Force an install method instead of auto-detecting. |
| `--source <path\|url>` | `-Source <path\|url>` | Install from somewhere else — a local clone, a fork. |
| `--ref <branch\|tag>` | `-Ref <branch\|tag>` | Install a specific git ref. Default `main`. |
| `--no-config` | `-NoConfig` | Do not create a starter configuration. |
| `--uninstall` | `-Uninstall` | Remove blindgrid, keeping your configuration. |
| `--help` | `Get-Help .\install.ps1` | Show the options. |

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
