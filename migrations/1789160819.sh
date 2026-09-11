#!/bin/bash

# omarchy:summary=Arreglar crash de la Boutique inyectando comandos hyprctl en el entorno seguro de Omarchy
# omarchy:author=X64 Studios

# Reescribimos el binario para usar el motor hiperestable de Omarchy (org.omarchy.terminal)
# pero forzando el redimensionamiento dinámico desde adentro para burlar las reglas flotantes.
cat << 'EOF' > "$OMARCHY_PATH/bin/x64-launch-tiled-terminal"
#!/bin/bash
source omarchy-restart-gum
cmd="$*"
presentation_script="sleep 0.1; hyprctl dispatch togglefloating; $cmd; if (( \$? != 130 )); then omarchy-show-done; fi"
exec setsid uwsm-app -- xdg-terminal-exec --app-id=org.omarchy.terminal --title="X64 Boutique" -e bash -c "$presentation_script"
EOF

chmod +x "$OMARCHY_PATH/bin/x64-launch-tiled-terminal"
