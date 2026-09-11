#!/bin/bash

# omarchy:summary=Auto-Healing Final: Remover hl.command tóxicos e inyectar sintaxis windowrulev2 válida
# omarchy:author=X64 Studios

HYPR_CONF="$HOME/.config/hypr/hyprland.lua"

if [[ -f "$HYPR_CONF" ]]; then
    # 1. Purga absoluta de intentos anteriores
    sed -i '/X64 Studios: Modo Gaming Automático/d' "$HYPR_CONF"
    sed -i '/hl\.command/d' "$HYPR_CONF"
    sed -i '/windowrulev2 = /d' "$HYPR_CONF"

    # 2. Inyección de la sintaxis estricta y correcta que hl.config acepta
    cat << 'EOF' >> "$HYPR_CONF"

-- X64 Studios: Modo Gaming Automático (Cero Latencia)
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
EOF
fi

# El updater reiniciará Hyprland automáticamente si hay cambios.
