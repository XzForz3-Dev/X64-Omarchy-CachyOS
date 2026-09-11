#!/bin/bash

# omarchy:summary=Inyectar reglas de Modo Gaming Automático (Latencia Cero)
# omarchy:author=X64 Studios

HYPR_CONF="$HOME/.config/hypr/hyprland.lua"
LOOK_CONF="$HOME/.config/hypr/looknfeel.lua"

if [[ -f "$LOOK_CONF" ]]; then
  if ! grep -q "allow_tearing = true" "$LOOK_CONF"; then
    sed -i 's/general = {/general = {\n    allow_tearing = true, -- Requerido para Modo Gaming X64/' "$LOOK_CONF"
  fi
fi

if [[ -f "$HYPR_CONF" ]]; then
  if ! grep -q "Modo Gaming Automático" "$HYPR_CONF"; then
    cat << 'EOF' >> "$HYPR_CONF"

-- X64 Studios: Modo Gaming Automático (Cero Latencia)
o.window({ class = "^steam_app_.*$" }, { immediate = true, noanim = true, noblur = true, noshadow = true })
o.window({ class = "^gamescope$" }, { immediate = true, noanim = true, noblur = true, noshadow = true })
o.window({ class = "^cs2$" }, { immediate = true, noanim = true, noblur = true, noshadow = true })
EOF
  fi
fi
