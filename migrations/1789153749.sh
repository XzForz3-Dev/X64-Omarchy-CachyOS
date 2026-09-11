#!/bin/bash

# omarchy:summary=Auto-Healing: Reparar sintaxis de Modo Gaming y limpiar barra roja de Hyprland
# omarchy:author=X64 Studios

HYPR_CONF="$HOME/.config/hypr/hyprland.lua"
LOOK_CONF="$HOME/.config/hypr/looknfeel.lua"

# 1. Curar looknfeel.lua (Remover inyecciones rotas y añadir bloque limpio)
if [[ -f "$LOOK_CONF" ]]; then
    # Borrar cualquier linea que tenga allow_tearing
    sed -i '/allow_tearing = true/d' "$LOOK_CONF"
    
    # Añadir al final del archivo de manera segura
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

# 2. Curar hyprland.lua (Remover o.window defectuoso y añadir hl.command)
if [[ -f "$HYPR_CONF" ]]; then
    # Borrar el bloque defectuoso antiguo
    sed -i '/X64 Studios: Modo Gaming Automático/d' "$HYPR_CONF"
    sed -i '/class = "\^steam_app_.\*\$"/d' "$HYPR_CONF"
    sed -i '/class = "\^gamescope\$"/d' "$HYPR_CONF"
    sed -i '/class = "\^cs2\$"/d' "$HYPR_CONF"

    # Inyectar el bloque curado nativo
    cat << 'EOF' >> "$HYPR_CONF"

-- X64 Studios: Modo Gaming Automático (Cero Latencia)
hl.command("windowrulev2 = immediate, class:^steam_app_.*$")
hl.command("windowrulev2 = noanim, class:^steam_app_.*$")
hl.command("windowrulev2 = noblur, class:^steam_app_.*$")
hl.command("windowrulev2 = noshadow, class:^steam_app_.*$")

hl.command("windowrulev2 = immediate, class:^gamescope$")
hl.command("windowrulev2 = noanim, class:^gamescope$")
hl.command("windowrulev2 = noblur, class:^gamescope$")
hl.command("windowrulev2 = noshadow, class:^gamescope$")

hl.command("windowrulev2 = immediate, class:^cs2$")
hl.command("windowrulev2 = noanim, class:^cs2$")
hl.command("windowrulev2 = noblur, class:^cs2$")
hl.command("windowrulev2 = noshadow, class:^cs2$")
EOF
fi

# Recargar hyprland silenciosamente para aplicar los cambios y quitar la barra roja
hyprctl reload >/dev/null 2>&1 || true
