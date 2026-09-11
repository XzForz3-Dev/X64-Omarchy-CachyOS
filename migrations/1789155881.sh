#!/bin/bash

# omarchy:summary=Sanación absoluta de Hyprland con recarga forzada en memoria
# omarchy:author=X64 Studios

HYPR_CONF="$HOME/.config/hypr/hyprland.lua"
LOOK_CONF="$HOME/.config/hypr/looknfeel.lua"

# 1. Purgar cualquier error fantasma en looknfeel.lua
if [[ -f "$LOOK_CONF" ]]; then
    sed -i '/allow_tearing = true/d' "$LOOK_CONF"
    if ! grep -q "Requerido para Modo Gaming X64" "$LOOK_CONF"; then
        cat << 'EOF' >> "$LOOK_CONF"

-- Auto-Healing X64: Permitir Tearing para latencia cero
hl.config({
  general = {
    allow_tearing = true, -- Requerido para Modo Gaming X64 (Latencia Cero)
  },
})
EOF
    fi
fi

# 2. Purgar sintaxis antigua de o.window o hl.command en hyprland.lua
if [[ -f "$HYPR_CONF" ]]; then
    sed -i '/X64 Studios: Modo Gaming/d' "$HYPR_CONF"
    sed -i '/class = "\^steam_app_.\*\$"/d' "$HYPR_CONF"
    sed -i '/class = "\^gamescope\$"/d' "$HYPR_CONF"
    sed -i '/class = "\^cs2\$"/d' "$HYPR_CONF"
    sed -i '/hl\.command/d' "$HYPR_CONF"
    sed -i '/windowrulev2 =/d' "$HYPR_CONF"

    # Inyectar bloque nativo seguro
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

# 3. Obligar a Hyprland a recargar la pantalla para borrar la barra roja vieja
hyprctl reload >/dev/null 2>&1 || true
