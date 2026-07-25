# Animated demo of the interactive flow, for https://github.com/charmbracelet/vhs
#
#   brew install vhs
#   uv venv && uv pip install -e ".[dev]"   # if you have not already
#   vhs docs/demo.tape
#
# Produces docs/demo.gif. Run it from the repository root.
#
# The hidden block below points the tool at a throwaway configuration, so
# recording the demo never touches your own config.toml.
#
# Every recording draws fresh numbers: the demo runs the real CSPRNG, like
# every other code path here.

Output docs/demo.gif

Set Shell bash
Set FontSize 16
Set Width 1120
Set Height 940
Set Padding 25
Set Theme "Catppuccin Mocha"
Set TypingSpeed 70ms

Hide
Type "export PS1='$ '" Enter
Type "export PATH=$PWD/.venv/bin:$PATH" Enter
Type `export BLINDGRID_CONFIG="$(mktemp -d)/config.toml"` Enter
Type "blindgrid config init -c $BLINDGRID_CONFIG" Enter
Type "clear" Enter
Show

Sleep 1s
Type "blindgrid generate --month 2026-09"
Sleep 600ms
Enter
Sleep 2s

# Budget prompt: well under the 40.00 ceiling from the example config.
Type "30"
Sleep 900ms
Enter
Sleep 1.5s

# Lottery checkbox: every entry starts ticked, so drop the third one.
Down
Sleep 500ms
Down
Sleep 500ms
Space
Sleep 1s
Enter
Sleep 6s
