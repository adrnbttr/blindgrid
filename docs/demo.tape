# Animated demo of the interactive flow, for https://github.com/charmbracelet/vhs
#
#   brew install vhs
#   vhs docs/demo.tape
#
# Produces docs/demo.gif. The static docs/demo.svg in the README is generated
# by docs/make_demo.py instead, and does not need vhs.

Output docs/demo.gif

Set Shell zsh
Set FontSize 15
Set Width 1200
Set Height 900
Set Padding 20
Set Theme "Catppuccin Mocha"
Set TypingSpeed 60ms

Type "blindgrid generate"
Sleep 500ms
Enter
Sleep 1.5s

# Budget prompt
Type "30"
Sleep 800ms
Enter
Sleep 1s

# Lottery checkbox: keep the first two, drop the third
Down
Down
Space
Sleep 800ms
Enter
Sleep 4s
