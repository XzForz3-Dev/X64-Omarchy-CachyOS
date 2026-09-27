#!/bin/bash
# ==============================================================================
# X64-Omarchy-CachyOS Installer Launcher (Python TUI Edition)
# By X64 Studios
# ==============================================================================

if ! python3 security_gateway.py; then
    echo -e "\n\033[1;31m[!] Autenticación fallida o abortada. Saliendo...\033[0m"
    exit 1
fi

# Mantener sudo vivo en segundo plano
while true; do sudo -n true; sleep 60; kill -0 "$$" || exit; done 2>/dev/null &

set -eEuo pipefail

if [ "$EUID" -eq 0 ]; then
  echo "⚠️ Error: Por favor, NO ejecutes este script como root."
  echo "Ejecútalo como tu usuario normal."
  exit 1
fi

clear
echo -e "\n[+] Verificando motor de interfaz..."
sudo rm -f x64-install.log 2>/dev/null || true
sudo sed -i '/NoExtract = usr\/share\/doc\/\*/d' /etc/pacman.conf 2>/dev/null || true

if ! command -v python3 &> /dev/null; then
    echo "Instalando dependencias base (Python)..."
    sudo pacman -Sy --noconfirm python >/dev/null 2>&1
fi

if ! python3 -c "import rich" &> /dev/null || ! command -v fastfetch &> /dev/null || ! python3 -c "import psutil" &> /dev/null; then
    echo "Descargando motor gráfico de terminal y dependencias..."
    sudo pacman -Sy --noconfirm python-rich fastfetch python-psutil >/dev/null 2>&1
fi

echo -e "\n[+] Sincronizando con la última versión..."
git pull --rebase --autostash 2>/dev/null || true
rm -rf __pycache__ 2>/dev/null || true

echo -e "\n[+] Iniciando X64-Omarchy TUI Installer..."
exec python3 x64-install.py
