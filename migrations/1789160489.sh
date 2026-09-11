#!/bin/bash

# omarchy:summary=Usar launcher personalizado x64-launch-tiled-terminal para la Boutique
# omarchy:author=X64 Studios

# Primero instalamos el nuevo binario en el sistema actual si no lo tiene
if [[ -d "/usr/share/omarchy/bin" ]]; then
    sudo cp -f "$OMARCHY_PATH/bin/x64-launch-tiled-terminal" "/usr/share/omarchy/bin/" 2>/dev/null || true
    sudo chmod +x "/usr/share/omarchy/bin/x64-launch-tiled-terminal" 2>/dev/null || true
fi

# Buscamos donde clonó el repositorio
REPO_DIR="$HOME/X64-Omarchy-CachyOS"
if [[ ! -d "$REPO_DIR" ]]; then
    REPO_DIR="$HOME/Proyectos/X64-Omarchy-CachyOS"
fi

cat << EOF > "$HOME/.local/share/applications/x64-boutique.desktop"
[Desktop Entry]
Name=X64 Software Boutique
Comment=Mega Dashboard y Selector de Paquetes
Exec=x64-launch-tiled-terminal "cd $REPO_DIR && ./x64-install.sh"
Icon=system-software-install
Terminal=false
Type=Application
Categories=System;Settings;
EOF
