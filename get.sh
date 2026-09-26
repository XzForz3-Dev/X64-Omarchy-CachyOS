#!/bin/bash
echo -e "\e[36m[X64 LIOS]\e[0m Preparando dependencias iniciales..."
sudo pacman -S --noconfirm --needed git python python-rich
cd /tmp
rm -rf X64-Omarchy-CachyOS
echo -e "\e[36m[X64 LIOS]\e[0m Descargando instalador maestro..."
git clone -b quattro https://github.com/XzForz3-Dev/X64-Omarchy-CachyOS.git
cd X64-Omarchy-CachyOS
echo -e "\e[36m[X64 LIOS]\e[0m Iniciando Dashboard..."
python3 x64-install.py
