#!/bin/bash

# omarchy:summary=Auto-Healing Definitivo Nivel Dios: Restaurar hyprland.lua por completo
# omarchy:author=X64 Studios

# En lugar de usar sed o Python, usamos la herramienta nativa de Omarchy
# para sobreescribir el archivo dañado con la versión perfecta del repositorio.
# Esto no borra las configuraciones del usuario porque están en bindings.lua y monitors.lua.
omarchy-refresh-config hypr/hyprland.lua

# Recargar Hyprland para limpiar la barra roja
hyprctl reload >/dev/null 2>&1 || true
