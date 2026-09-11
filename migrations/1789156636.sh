#!/bin/bash

# omarchy:summary=Auto-Healing Definitivo: Limpieza Quirúrgica de Sintaxis Lua
# omarchy:author=X64 Studios

HYPR_CONF="$HOME/.config/hypr/hyprland.lua"

if [[ -f "$HYPR_CONF" ]]; then
    python3 -c '
import sys

try:
    with open(sys.argv[1], "r") as f:
        content = f.read()

    start_marker = "-- X64 Studios: Modo Gaming"
    end_marker = "-- Hardware Video Acceleration"

    if start_marker in content and end_marker in content:
        before = content.split(start_marker)[0]
        after = end_marker + content.split(end_marker, 1)[1]
        
        new_block = """-- X64 Studios: Modo Gaming Automático (Cero Latencia)
hl.config({
  windowrulev2 = {
    "immediate, class:^steam_app_.*$",
    "noanim, class:^steam_app_.*$",
    "noblur, class:^steam_app_.*$",
    "noshadow, class:^steam_app_.*$",
    "immediate, class:^gamescope$",
    "noanim, class:^gamescope$",
    "noblur, class:^gamescope$",
    "noshadow, class:^gamescope$",
    "immediate, class:^cs2$",
    "noanim, class:^cs2$",
    "noblur, class:^cs2$",
    "noshadow, class:^cs2$"
  }
})

"""
        new_content = before + new_block + after
        with open(sys.argv[1], "w") as f:
            f.write(new_content)
except Exception as e:
    pass
' "$HYPR_CONF"
fi

hyprctl reload >/dev/null 2>&1 || true
