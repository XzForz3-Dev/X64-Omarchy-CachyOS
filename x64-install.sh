#!/bin/bash
# ==============================================================================
# X64-Omarchy-CachyOS Installer Launcher (Python TUI Edition)
# By X64 Studios
# ==============================================================================

set -eEuo pipefail

if [ "$EUID" -eq 0 ]; then
  echo "⚠️ Error: Por favor, NO ejecutes este script como root."
  echo "Ejecútalo como tu usuario normal."
  exit 1
fi

clear
echo -e "\n🔒 Este instalador requiere permisos de administrador."
sudo -v

echo -e "\n[+] Verificando motor de interfaz..."
if ! command -v python3 &> /dev/null; then
    echo "Instalando dependencias base (Python)..."
    sudo pacman -Sy --noconfirm python >/dev/null 2>&1
fi

if ! python3 -c "import rich" &> /dev/null; then
    echo "Descargando motor gráfico de terminal (python-rich)..."
    sudo pacman -Sy --noconfirm python-rich >/dev/null 2>&1
fi

echo -e "\n[+] Iniciando X64-Omarchy TUI Installer..."
exec python3 x64-install.py
