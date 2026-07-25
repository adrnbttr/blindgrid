# Installation guide

The short version, if you just want it working:

```bash
curl -fsSL https://raw.githubusercontent.com/adrnbttr/blindgrid/main/install.sh | bash
```

The rest of this page is for when that is not what you want, or when it does
not go to plan.

## What the installer does

It installs into your home directory and nowhere else. Specifically:

1. Looks for `uv`, then `pipx`, then a Python 3.11 or newer on your `PATH`.
2. Installs blindgrid with the first of those it finds.
3. Writes a starter `config.toml` to `~/.config/blindgrid/`, unless one is
   already there.
4. Tells you whether the install directory is on your `PATH`, and exactly what
   to add if it is not.

It never runs `sudo`, never writes outside `$HOME`, and never installs a
third-party tool behind your back — if neither uv nor pipx is present, it falls
back to a plain virtualenv built with the Python you already have.

### Reading it before running it

Piping a script from the internet into a shell means trusting whoever controls
that URL. If you would rather look first:

```bash
curl -fsSLO https://raw.githubusercontent.com/adrnbttr/blindgrid/main/install.sh
less install.sh
bash install.sh
```

The script is about 250 lines, and shellcheck runs against it in CI.

### Options

| Option | Effect |
| --- | --- |
| `--method uv\|pipx\|venv` | Force an install method instead of auto-detecting. |
| `--source <path\|url>` | Install from somewhere else — a local clone, a fork. |
| `--ref <branch\|tag>` | Install a specific git ref. Default `main`. |
| `--no-config` | Do not create a starter configuration. |
| `--uninstall` | Remove blindgrid, keeping your configuration. |
| `--help` | Show the options. |

Environment: `BLINDGRID_PREFIX` changes the install prefix (default
`~/.local`), and `NO_COLOR` turns off colour.

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
  Most terminals from the last decade are fine.
- No database, no network access at runtime, no account. The tool reads a TOML
  file and writes a Markdown one.

If your system Python is too old:

```bash
brew install python@3.12                 # macOS
sudo apt install python3.12 python3.12-venv   # Debian, Ubuntu
```

## After installing

```bash
blindgrid config show     # where is my config, what is in it
blindgrid generate        # plan this month
```

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
line to add; it is usually:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

Put that in `~/.zshrc` (zsh, the default on macOS) or `~/.bashrc`, then open a
new terminal. With uv you can also run `uv tool update-shell`.

### `No configuration found at ...`

Nothing has created a config yet:

```bash
blindgrid config init
```

blindgrid looks for one in this order: `$BLINDGRID_CONFIG`, then `config.toml`
in the current directory, then `~/.config/blindgrid/config.toml`. The
current-directory rule means you can keep a separate setup per folder without
touching the global one.

### `error: externally-managed-environment`

Your system Python refuses direct `pip install`, which is correct of it. Use
uv or pipx, or the installer, which handles this for you. Do not pass
`--break-system-packages`.

### The tables look like mojibake

Your terminal is not in a UTF-8 locale:

```bash
export LANG=en_US.UTF-8
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

Or `uv tool upgrade blindgrid` / `pipx upgrade blindgrid`.

## Uninstalling

```bash
curl -fsSL https://raw.githubusercontent.com/adrnbttr/blindgrid/main/install.sh | bash -s -- --uninstall
```

Or, from a clone, `bash install.sh --uninstall`.

Your configuration is deliberately left behind. Remove it yourself:

```bash
rm -rf ~/.config/blindgrid
```
