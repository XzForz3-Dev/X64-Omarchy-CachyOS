#!/bin/bash

# omarchy:summary=Crear icono de escritorio para X64 Software Boutique
# omarchy:author=X64 Studios

mkdir -p ~/.local/share/applications

# Buscamos donde clonó el repositorio (normalmente ~/X64-Omarchy-CachyOS)
REPO_DIR="$HOME/X64-Omarchy-CachyOS"
if [[ ! -d "$REPO_DIR" ]]; then
    REPO_DIR="$HOME/Proyectos/X64-Omarchy-CachyOS"
fi

cat << EOF > ~/.local/share/applications/x64-boutique.desktop
[Desktop Entry]
Name=X64 Software Boutique
Comment=Mega Dashboard y Selector de Paquetes
Exec=kitty --hold -e bash -c "cd $REPO_DIR && ./x64-install.sh"
Icon=system-software-install
Terminal=false
Type=Application
Categories=System;Settings;
EOF

# También inyectamos el cartel de rescate TTY en sddm
if [[ -d /usr/share/sddm/themes/omarchy ]]; then
    sudo sed -i 's/placeholderText: "Password"/placeholderText: "🚑 ¿Pantalla Negra? Presiona Ctrl+Alt+F2"/g' /usr/share/sddm/themes/omarchy/Main.qml 2>/dev/null || true
fi
