#!/bin/bash

# omarchy:summary=Eliminar regla flotante de la Boutique para que se ejecute a pantalla completa
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
Exec=uwsm-app -- xdg-terminal-exec --app-id=org.x64.boutique --title="X64 Boutique" -e bash -c "cd $REPO_DIR && ./x64-install.sh; echo 'Boutique finalizada. Presiona Enter para cerrar...'; read"
Icon=system-software-install
Terminal=false
Type=Application
Categories=System;Settings;
EOF
