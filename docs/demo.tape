# Animated demo, for https://github.com/charmbracelet/vhs
#
#   brew install vhs
#   uv venv && uv pip install -e ".[dev]"   # if you have not already
#   vhs docs/demo.tape
#
# Produces docs/demo.gif. Run it from the repository root.
#
# The hidden blocks below build a throwaway config and plan in a temporary
# directory, so recording the demo never touches your own.
#
# Every recording draws fresh numbers: the demo runs the real CSPRNG, like
# every other code path here.

Output docs/demo.gif

Set Shell bash
Set FontSize 16
Set Width 1180
Set Height 1160
Set Padding 25
Set Theme "Catppuccin Mocha"
Set TypingSpeed 65ms

Hide
Type "export PS1='$ '" Enter
Type "export PATH=$PWD/.venv/bin:$PATH" Enter
Type `export BG=$(mktemp -d)` Enter
Type `export BLINDGRID_CONFIG="$BG/config.toml" BLINDGRID_STATE="$BG/plan.json"` Enter
Type "blindgrid config init -c $BLINDGRID_CONFIG" Enter
# Two people, each with their own ceiling and their own games.
Type `printf '\n[[player]]\nname = "Adrien"\nmax_monthly_budget = 40.00\n  [player.weight]\n  EuroMillions = 1.0\n  Loto = 1.0\n  EuroDreams = 0.4\n\n[[player]]\nname = "Marie"\nmax_monthly_budget = 25.00\n  [player.weight]\n  Loto = 1.0\n  EuroDreams = 1.0\n' >> "$BLINDGRID_CONFIG"` Enter
Type "cd $BG && clear" Enter
Show

Sleep 1s

# Who plays, and what each of them plays.
Type "blindgrid player list"
Sleep 400ms
Enter
Sleep 3.5s

Type "clear"
Enter
Sleep 500ms

# The month is planned for the household in one go.
Type "blindgrid generate --month 2026-09"
Sleep 600ms
Enter
Sleep 1.8s

# Each person is asked for their own budget, against their own ceiling.
Type "20"
Sleep 700ms
Enter
Sleep 1.2s
Type "12"
Sleep 700ms
Enter
Sleep 7s

Type "clear"
Enter
Sleep 500ms

# Running it again returns the same plan rather than drawing a new one.
Type "blindgrid generate --month 2026-09"
Sleep 600ms
Enter
Sleep 6s
