echo "Update calculator shortcut to Super + Ctrl + Q to avoid resizing conflicts"

if [[ -f ~/.config/hypr/bindings/utilities.lua ]]; then
  sed -i 's/SUPER + SHIFT + EQUAL/SUPER + CTRL + Q/g' ~/.config/hypr/bindings/utilities.lua
fi
