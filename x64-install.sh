#!/bin/bash
# ==============================================================================
# X64-Omarchy-CachyOS Installer
# By X64 Studios
# ==============================================================================

set -e

# Colores para mejor legibilidad en CLI
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "=========================================================="
echo "    X64 Studios - Omarchy CachyOS Automated Installer     "
echo "=========================================================="
echo -e "${NC}"

# Pre-flight check: No ejecutar como root
if [ "$EUID" -eq 0 ]; then
  echo -e "${RED}Error: Por favor, NO ejecutes este script como root.${NC}"
  echo "Ejecútalo como tu usuario normal. Se te pedirá contraseña para sudo cuando sea necesario."
  exit 1
fi

# Pre-flight check: Internet
if ! ping -c 1 archlinux.org > /dev/null 2>&1; then
  echo -e "${RED}Error: No hay conexión a internet. Verifica tu red y vuelve a intentarlo.${NC}"
  exit 1
fi

echo -e "${GREEN}[1.5/5] Inyectando repositorio privado de Omarchy...${NC}"
if ! grep -q "omarchy" /etc/pacman.conf; then
  sudo bash -c 'echo -e "\n[omarchy]\nSigLevel = Optional TrustAll\nServer = https://pkgs.omarchy.org/\$arch/\n" >> /etc/pacman.conf'
fi

echo -e "${GREEN}[2/5] Sincronizando repositorios...${NC}"
if ! sudo pacman -Syu --noconfirm; then
  echo -e "${RED}⚠️ Detectado problema con las firmas de CachyOS. Reparando llavero automáticamente...${NC}"
  sudo rm -rf /etc/pacman.d/gnupg/
  sudo pacman-key --init
  sudo pacman-key --populate archlinux cachyos
  echo -e "${GREEN}Llavero reparado. Reintentando sincronización...${NC}"
  sudo pacman -Syu --noconfirm
fi

echo -e "${GREEN}[2/5] Recopilando dependencias mapeadas...${NC}"
# Combinamos nuestros dos archivos purificados de dependencias
ALL_PACKAGES=$(cat install/omarchy-base.packages install/omarchy-other.packages | grep -v '^#' | grep -v '^$' | tr '\n' ' ')

# Filtramos solo los paquetes que faltan por instalar para evitar la lista enorme de "advertencias"
MISSING_PACKAGES=$(pacman -T $ALL_PACKAGES || true)

echo -e "${GREEN}[3/5] Instalando el núcleo de Omarchy (Wayland, Hyprland, Firefox, UI)...${NC}"
if [ -n "$MISSING_PACKAGES" ]; then
  # Removemos jack2 si existe, porque entra en conflicto directo con pipewire-jack
  sudo pacman -Rdd --noconfirm jack2 2>/dev/null || true
  
  # Instalamos silenciosamente los que faltan
  sudo pacman -S --noconfirm $MISSING_PACKAGES
else
  echo "Todos los paquetes ya están instalados."
fi

echo -e "${GREEN}[4/5] Aplicando El Escudo (Copiando Dotfiles y Configuraciones)...${NC}"
# Nos aseguramos que las carpetas existan
mkdir -p ~/.config ~/.local/bin ~/.local/share/themes
sudo mkdir -p /usr/share/omarchy

# Instalamos el núcleo de Omarchy en el sistema global (Requerido por Hyprland/Lua)
sudo cp -r bin config default shell themes /usr/share/omarchy/ 2>/dev/null || true
sudo chmod -R 755 /usr/share/omarchy

# Registrar sesión oficial en el gestor de inicio (SDDM)
sudo mkdir -p /usr/share/wayland-sessions
sudo cp default/wayland-sessions/omarchy.desktop /usr/share/wayland-sessions/ 2>/dev/null || true

# Exportar OMARCHY_PATH globalmente para que funcionen los scripts del sistema
sudo bash -c 'echo "export OMARCHY_PATH=/usr/share/omarchy" > /etc/profile.d/omarchy.sh'
sudo chmod +x /etc/profile.d/omarchy.sh

# Copiamos los dotfiles al directorio del usuario para permitir personalización
cp -r config/* ~/.config/ 2>/dev/null || true
cp -r bin/* ~/.local/bin/ 2>/dev/null || true
cp -r themes/* ~/.local/share/themes/ 2>/dev/null || true

# Hacemos que todos los binarios locales sean ejecutables
chmod +x ~/.local/bin/* 2>/dev/null || true

echo -e "${GREEN}[5/5] Activando Servicios Críticos...${NC}"
sudo systemctl enable sddm.service --now 2>/dev/null || true
sudo systemctl enable bluetooth.service 2>/dev/null || true

echo -e "${GREEN}[6/6] Inicializando Tema y Entorno (Tokyo Night)...${NC}"
export OMARCHY_PATH=/usr/share/omarchy
/usr/share/omarchy/bin/omarchy-theme-set "Tokyo Night" 2>/dev/null || true

echo -e "======================================================="
echo -e "${GREEN}¡Instalación de Omarchy Completada con Éxito!${NC}"
echo "      Tu sistema CachyOS ahora tiene el escudo Omarchy.   "
echo "=========================================================="
echo -e "${NC}"
echo "Recomendación: Reinicia el equipo ahora."
