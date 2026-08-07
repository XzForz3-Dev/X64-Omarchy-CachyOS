echo "Revert monitor scaling to 1 to prevent unexpected x2 zoom"

if [[ -f ~/.config/hypr/monitors.lua ]]; then
  sed -i 's/local omarchy_monitor_scale = "auto"/local omarchy_monitor_scale = 1/g' ~/.config/hypr/monitors.lua
fi
