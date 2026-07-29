#!/bin/bash
# ==============================================================================
# X64-Omarchy-CachyOS Installer Launcher (Python TUI Edition)
# By X64 Studios
# ==============================================================================

# Solicitar contraseña de sudo una sola vez al principio
sudo -v
# Mantener sudo vivo en segundo plano
while true; do sudo -n true; sleep 60; kill -0 "$$" || exit; done 2>/dev/null &

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

if ! python3 -c "import rich" &> /dev/null || ! command -v gum &> /dev/null || ! command -v fastfetch &> /dev/null || ! python3 -c "import psutil" &> /dev/null; then
    echo "Descargando motor gráfico de terminal y dependencias..."
    sudo pacman -Sy --noconfirm python-rich gum fastfetch python-psutil >/dev/null 2>&1
fi

echo -e "\n[+] Iniciando X64-Omarchy TUI Installer..."
exec python3 x64-install.py
