#!/usr/bin/env bash
#
# blindgrid installer.
#
#   curl -fsSL https://raw.githubusercontent.com/adrnbttr/blindgrid/main/install.sh | bash
#
# Installs into your home directory only. It never asks for sudo, never writes
# outside $HOME, and never installs a third-party tool without saying so: if
# neither uv nor pipx is present it falls back to a plain virtualenv built with
# the Python you already have.
#
# Options:
#   --method auto|uv|pipx|venv   How to install. Default: auto (uv, then pipx, then venv).
#   --source <path|url>          What to install. Default: the published package.
#   --ref <branch|tag>           Git ref to install. Default: main.
#   --no-config                  Skip creating a starter configuration file.
#   --uninstall                  Remove blindgrid, keeping your configuration.
#   --help                       Show this help.
#
# Environment:
#   BLINDGRID_PREFIX   Install prefix. Default: ~/.local
#   NO_COLOR           Disable colour output.

set -euo pipefail

REPO_URL="https://github.com/adrnbttr/blindgrid"
MIN_MAJOR=3
MIN_MINOR=11
PREFIX="${BLINDGRID_PREFIX:-$HOME/.local}"
VENV_DIR="$PREFIX/share/blindgrid/venv"
BIN_DIR="$PREFIX/bin"
CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/blindgrid"
STATE_DIR="${XDG_STATE_HOME:-$HOME/.local/state}/blindgrid"

METHOD="auto"
SOURCE=""
REF="main"
CREATE_CONFIG=1
UNINSTALL=0

# ---------------------------------------------------------------- presentation

if [ -t 1 ] && [ -z "${NO_COLOR:-}" ] && [ "${TERM:-dumb}" != "dumb" ]; then
  BOLD=$'\033[1m'; DIM=$'\033[2m'; RED=$'\033[31m'; GREEN=$'\033[32m'
  YELLOW=$'\033[33m'; CYAN=$'\033[36m'; RESET=$'\033[0m'
else
  BOLD=""; DIM=""; RED=""; GREEN=""; YELLOW=""; CYAN=""; RESET=""
fi

case "${LC_ALL:-}${LC_CTYPE:-}${LANG:-}" in
  *UTF-8*|*utf8*|*UTF8*) TICK="✓"; CROSS="✗"; WARN_MARK="!"; BULLET="·" ;;
  *)                     TICK="+"; CROSS="x"; WARN_MARK="!"; BULLET="-" ;;
esac

step() { printf '%s%s%s %s\n' "$CYAN" "$BULLET" "$RESET" "$1"; }
ok()   { printf '  %s%s%s %s\n' "$GREEN" "$TICK" "$RESET" "$1"; }
warn() { printf '  %s%s%s %s\n' "$YELLOW" "$WARN_MARK" "$RESET" "$1"; }
info() { printf '    %s%s%s\n' "$DIM" "$1" "$RESET"; }

die() {
  printf '\n  %s%s %s%s\n\n' "$RED" "$CROSS" "$1" "$RESET" >&2
  exit 1
}

banner() {
  printf '\n  %sblindgrid%s %s%s%s lottery grids from cryptographic randomness\n\n' \
    "$BOLD" "$RESET" "$DIM" "$BULLET" "$RESET"
}

usage() {
  # The header comment of this file is the help text. Print it back, minus the
  # shebang, stopping at the first line that is not a comment.
  awk 'NR == 1 { next } /^#/ { sub(/^# ?/, ""); print; next } { exit }' "$0"
  exit 0
}

have() { command -v "$1" >/dev/null 2>&1; }

# ------------------------------------------------------------------- arguments

while [ $# -gt 0 ]; do
  case "$1" in
    --method)     METHOD="${2:-}"; shift 2 ;;
    --source)     SOURCE="${2:-}"; shift 2 ;;
    --ref)        REF="${2:-}"; shift 2 ;;
    --no-config)  CREATE_CONFIG=0; shift ;;
    --uninstall)  UNINSTALL=1; shift ;;
    --help|-h)    usage ;;
    *)            die "Unknown option: $1. Try --help." ;;
  esac
done

case "$METHOD" in
  auto|uv|pipx|venv) ;;
  *) die "Unknown method: $METHOD. Expected auto, uv, pipx or venv." ;;
esac

# The published package by default; --ref switches to GitHub at that ref.
if [ -z "$SOURCE" ]; then
  if [ "$REF" = "main" ]; then SOURCE="blindgrid"; else SOURCE="git+$REPO_URL.git@$REF"; fi
fi

# ----------------------------------------------------------------- uninstalling

uninstall() {
  banner
  step "Removing blindgrid"
  local removed=0

  if have uv && uv tool list 2>/dev/null | grep -q '^blindgrid'; then
    uv tool uninstall blindgrid >/dev/null 2>&1 && ok "removed the uv tool" && removed=1
  fi

  if have pipx && pipx list --short 2>/dev/null | grep -q '^blindgrid'; then
    pipx uninstall blindgrid >/dev/null 2>&1 && ok "removed the pipx package" && removed=1
  fi

  if [ -d "$VENV_DIR" ]; then
    rm -rf "$VENV_DIR"
    rmdir "$(dirname "$VENV_DIR")" 2>/dev/null || true
    ok "removed $VENV_DIR"
    removed=1
  fi

  if [ -L "$BIN_DIR/blindgrid" ] || [ -f "$BIN_DIR/blindgrid" ]; then
    rm -f "$BIN_DIR/blindgrid"
    ok "removed $BIN_DIR/blindgrid"
    removed=1
  fi

  [ "$removed" -eq 1 ] || warn "nothing to remove"

  if [ -d "$CONFIG_DIR" ] || [ -d "$STATE_DIR" ]; then
    printf '\n'
    info "Your own files are untouched:"
    [ -d "$CONFIG_DIR" ] && info "  $CONFIG_DIR    (your budget ceiling and lotteries)"
    [ -d "$STATE_DIR" ]  && info "  $STATE_DIR    (the plan for the current month)"
    info "Delete them yourself if you want them gone."
  fi
  printf '\n'
  exit 0
}

[ "$UNINSTALL" -eq 1 ] && uninstall

# -------------------------------------------------------------- python lookup

# Echoes the path of the first interpreter that is new enough, or nothing.
find_python() {
  local candidate version
  for candidate in python3.13 python3.12 python3.11 python3 python; do
    have "$candidate" || continue
    version=$("$candidate" -c 'import sys; print("%d %d" % sys.version_info[:2])' 2>/dev/null) || continue
    # shellcheck disable=SC2086
    set -- $version
    if [ "$1" -gt "$MIN_MAJOR" ] || { [ "$1" -eq "$MIN_MAJOR" ] && [ "$2" -ge "$MIN_MINOR" ]; }; then
      command -v "$candidate"
      return 0
    fi
  done
  return 1
}

python_hint() {
  if [ "$(uname -s)" = "Darwin" ]; then
    info "brew install python@3.12"
  else
    info "sudo apt install python3.12-venv    # or your distribution's equivalent"
  fi
  info "Alternatively install uv, which brings its own Python:"
  info "curl -LsSf https://astral.sh/uv/install.sh | sh"
}

# ------------------------------------------------------------------ installing

install_with_uv() {
  step "Installing with uv"
  uv tool install --force --python ">=$MIN_MAJOR.$MIN_MINOR" "$SOURCE" 2>&1 | sed 's/^/    /'
  ok "installed"
  # uv keeps the environment out of sight and exposes a launcher here. Point at
  # the launcher, not the internal directory, or the PATH advice below sends
  # people to a directory uv never intended them to use.
  INSTALLED_BIN="${UV_TOOL_BIN_DIR:-${XDG_BIN_HOME:-$HOME/.local/bin}}/blindgrid"
}

install_with_pipx() {
  step "Installing with pipx"
  pipx install --force "$SOURCE" 2>&1 | sed 's/^/    /'
  ok "installed"
  INSTALLED_BIN="${PIPX_BIN_DIR:-$HOME/.local/bin}/blindgrid"
}

install_with_venv() {
  local python
  python="$(find_python)" || {
    printf '\n'
    warn "No Python $MIN_MAJOR.$MIN_MINOR or newer found."
    python_hint
    die "Cannot continue without a suitable Python."
  }

  step "Installing into a dedicated virtualenv"
  info "$("$python" --version 2>&1) at $python"

  mkdir -p "$(dirname "$VENV_DIR")" "$BIN_DIR"
  rm -rf "$VENV_DIR"
  "$python" -m venv "$VENV_DIR" || die "Could not create a virtualenv. Is python3-venv installed?"

  "$VENV_DIR/bin/python" -m pip install --quiet --upgrade pip >/dev/null 2>&1 || true
  "$VENV_DIR/bin/python" -m pip install --quiet "$SOURCE" 2>&1 | sed 's/^/    /'

  ln -sf "$VENV_DIR/bin/blindgrid" "$BIN_DIR/blindgrid"
  ok "installed into $VENV_DIR"
  ok "linked $BIN_DIR/blindgrid"
  INSTALLED_BIN="$BIN_DIR/blindgrid"
}

choose_method() {
  case "$METHOD" in
    uv)   have uv   || die "uv is not installed. See https://docs.astral.sh/uv/"; echo uv ;;
    pipx) have pipx || die "pipx is not installed. See https://pipx.pypa.io/"; echo pipx ;;
    venv) echo venv ;;
    auto)
      if have uv; then echo uv
      elif have pipx; then echo pipx
      else echo venv
      fi ;;
  esac
}

# ----------------------------------------------------------------- post-install

on_path() {
  case ":$PATH:" in *":$1:"*) return 0 ;; *) return 1 ;; esac
}

shell_rc() {
  case "$(basename "${SHELL:-}")" in
    zsh)  echo "$HOME/.zshrc" ;;
    bash) [ "$(uname -s)" = "Darwin" ] && echo "$HOME/.bash_profile" || echo "$HOME/.bashrc" ;;
    fish) echo "$HOME/.config/fish/config.fish" ;;
    *)    echo "your shell's startup file" ;;
  esac
}

check_path() {
  local dir
  dir="$(dirname "$INSTALLED_BIN")"
  if on_path "$dir"; then
    ok "$dir is already on your PATH"
    return
  fi

  warn "$dir is not on your PATH"
  info "Add this line to $(shell_rc), then restart your shell:"
  # shellcheck disable=SC2016  # $PATH is printed for the user to copy, not expanded here.
  printf '\n      %sexport PATH="%s:$PATH"%s\n\n' "$BOLD" "$dir" "$RESET"
}

create_config() {
  [ "$CREATE_CONFIG" -eq 1 ] || return 0

  step "Configuration"
  if [ -f "$CONFIG_DIR/config.toml" ]; then
    ok "keeping the existing $CONFIG_DIR/config.toml"
    return 0
  fi

  mkdir -p "$CONFIG_DIR"
  if "$INSTALLED_BIN" config init --config "$CONFIG_DIR/config.toml" >/dev/null 2>&1; then
    ok "wrote a starter config to $CONFIG_DIR/config.toml"
    info "It ships three French games as examples. Check the prices, the draw"
    info "days and above all max_monthly_budget before you play."
  else
    warn "could not write a starter config"
    info "Run 'blindgrid config init' yourself once blindgrid is on your PATH."
  fi
}

farewell() {
  local version
  version="$("$INSTALLED_BIN" version 2>/dev/null || echo "blindgrid")"

  printf '\n  %s%s installed%s\n\n' "$BOLD" "$version" "$RESET"
  printf '  Next:\n'
  printf '    %sblindgrid config show%s      %s%s see what is configured%s\n' \
    "$BOLD" "$RESET" "$DIM" "$BULLET" "$RESET"
  printf '    %sblindgrid generate%s         %s%s plan this month%s\n' \
    "$BOLD" "$RESET" "$DIM" "$BULLET" "$RESET"
  printf '\n  %sThis tool predicts nothing. Lottery draws are independent events,%s\n' "$DIM" "$RESET"
  printf '  %sand no combination is more likely than another.%s\n\n' "$DIM" "$RESET"
  printf '  Docs: %s%s\n\n' "$REPO_URL" ""
}

# ------------------------------------------------------------------------ main

banner

step "Checking your environment"
if have uv; then ok "uv found"; fi
if have pipx; then ok "pipx found"; fi
if python_path="$(find_python)"; then
  ok "$("$python_path" --version 2>&1)"
else
  warn "no Python $MIN_MAJOR.$MIN_MINOR or newer on PATH"
fi

INSTALLED_BIN=""
case "$(choose_method)" in
  uv)   install_with_uv ;;
  pipx) install_with_pipx ;;
  venv) install_with_venv ;;
esac

[ -x "$INSTALLED_BIN" ] || die "Installation finished but $INSTALLED_BIN is not executable."

step "Verifying"
"$INSTALLED_BIN" version >/dev/null 2>&1 || die "The installed binary does not run."
ok "blindgrid runs"

create_config
check_path
farewell
