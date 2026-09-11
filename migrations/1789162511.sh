#!/bin/bash

# omarchy:summary=Usar ejecución directa de foot para garantizar estabilidad TTY y tiling real
# omarchy:author=X64 Studios

cat << 'EOF' > "$OMARCHY_PATH/bin/x64-launch-tiled-terminal"
#!/bin/bash
source omarchy-restart-gum
cmd="$*"
presentation_script="omarchy-show-logo; $cmd; if (( \$? != 130 )); then omarchy-show-done; fi"

if command -v foot >/dev/null; then
    # Lanzamos foot directamente. Al ser el terminal base de Omarchy, sabemos que no
    # romperá Python (sys.stdout). Y al forzar un app-id custom, Hyprland lo pondrá en Tiling.
    exec setsid uwsm-app -- foot -a org.x64.boutique -T "X64 Boutique" bash -c "$presentation_script"
else
    # Fallback ultra seguro si por alguna extraña razón foot no existe
    exec setsid uwsm-app -- xdg-terminal-exec --app-id=org.omarchy.terminal --title="X64 Boutique" -e bash -c "sleep 0.2; hyprctl dispatch fullscreen 1; $presentation_script"
fi
EOF

chmod +x "$OMARCHY_PATH/bin/x64-launch-tiled-terminal"
