#!/bin/bash

# omarchy:summary=Arreglar el timing de maximización inyectando hyprctl asincrónico
# omarchy:author=X64 Studios

cat << 'EOF' > "$OMARCHY_PATH/bin/x64-launch-tiled-terminal"
#!/bin/bash
source omarchy-restart-gum
cmd="$*"
# Ejecutar hyprctl en segundo plano para asegurar que la ventana esté lista
presentation_script="(sleep 0.5 && hyprctl dispatch fullscreen 1) & $cmd; if (( \$? != 130 )); then omarchy-show-done; fi"
exec setsid uwsm-app -- xdg-terminal-exec --app-id=org.omarchy.terminal --title="X64 Boutique" -e bash -c "$presentation_script"
EOF

chmod +x "$OMARCHY_PATH/bin/x64-launch-tiled-terminal"
