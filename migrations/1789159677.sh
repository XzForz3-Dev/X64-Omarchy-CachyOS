#!/bin/bash

# omarchy:summary=Usar el wrapper nativo de Omarchy para lanzar la Boutique sin problemas de TTY
# omarchy:author=X64 Studios

# Buscamos donde clonó el repositorio (normalmente ~/X64-Omarchy-CachyOS)
REPO_DIR="$HOME/X64-Omarchy-CachyOS"
if [[ ! -d "$REPO_DIR" ]]; then
    REPO_DIR="$HOME/Proyectos/X64-Omarchy-CachyOS"
fi

cat << EOF > "$HOME/.local/share/applications/x64-boutique.desktop"
[Desktop Entry]
Name=X64 Software Boutique
Comment=Mega Dashboard y Selector de Paquetes
Exec=omarchy-launch-floating-terminal-with-presentation "cd $REPO_DIR && ./x64-install.sh"
Icon=system-software-install
Terminal=false
Type=Application
Categories=System;Settings;
EOF
