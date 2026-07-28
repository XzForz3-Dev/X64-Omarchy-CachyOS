#!/bin/bash
# ==============================================================================
# X64-Omarchy-CachyOS Installer - Pro Edition
# By X64 Studios
# ==============================================================================

set -eEuo pipefail

# Colores para mejor legibilidad en CLI
GREEN='\033[1;32m'
BLUE='\033[1;34m'
CYAN='\033[1;36m'
RED='\033[1;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Función de manejo de errores
error_handler() {
    local line=$1
    local cmd=$2
    echo -e "\n${RED}==========================================================${NC}"
    echo -e "${RED}❌ ERROR CRÍTICO DETECTADO${NC}"
    echo -e "${RED}Línea: ${NC}$line"
    echo -e "${RED}Comando fallido: ${NC}$cmd"
    echo -e "${RED}El instalador se ha detenido para proteger tu sistema.${NC}"
    echo -e "${RED}==========================================================${NC}\n"
    exit 1
}

trap 'error_handler $LINENO "$BASH_COMMAND"' ERR

# Limpiar pantalla y mostrar ASCII Art
clear
echo -e "${CYAN}"
cat << "EOF"
██╗  ██╗ ██████╗ ██╗  ██╗    ███████╗████████╗██╗   ██╗██████╗ ██╗ ██████╗ ███████╗
╚██╗██╔╝██╔════╝ ██║  ██║    ██╔════╝╚══██╔══╝██║   ██║██╔══██╗██║██╔═══██╗██╔════╝
 ╚███╔╝ ███████╗ ███████║    ███████╗   ██║   ██║   ██║██║  ██║██║██║   ██║███████╗
 ██╔██╗ ██╔═══██╗╚════██║    ╚════██║   ██║   ██║   ██║██║  ██║██║██║   ██║╚════██║
██╔╝ ██╗╚██████╔╝     ██║    ███████║   ██║   ╚██████╔╝██████╔╝██║╚██████╔╝███████║
╚═╝  ╚═╝ ╚═════╝      ╚═╝    ╚══════╝   ╚═╝    ╚═════╝ ╚═════╝ ╚═╝ ╚═════╝ ╚══════╝
EOF
echo -e "${NC}"
echo -e "${BLUE}==========================================================${NC}"
echo -e "${GREEN}  Bienvenido al Instalador de X64-Omarchy para CachyOS    ${NC}"
echo -e "${BLUE}==========================================================${NC}\n"

# Pre-flight check: No ejecutar como root
if [ "$EUID" -eq 0 ]; then
  echo -e "${RED}⚠️ Error: Por favor, NO ejecutes este script como root.${NC}"
  echo "Ejecútalo como tu usuario normal. El script pedirá contraseña para sudo automáticamente."
  exit 1
fi

# Pre-flight check: Internet
echo -e "${CYAN}Verificando conexión a internet...${NC}"
if ! ping -c 1 archlinux.org > /dev/null 2>&1; then
  echo -e "${RED}⚠️ Error: No hay conexión a internet. Verifica tu red y vuelve a intentarlo.${NC}"
  exit 1
fi
echo -e "${GREEN}✓ Conexión establecida.${NC}\n"

read -p "$(echo -e ${YELLOW}Presiona ENTER para iniciar la metamorfosis de tu sistema...${NC})"

echo -e "\n${GREEN}[1/6] Preparando el terreno (Llaveros y Bloqueos)...${NC}"
# Reparador automático del bloqueo de pacman
if [ -f /var/lib/pacman/db.lck ]; then
    echo -e "${YELLOW}⚠️ Bloqueo de Pacman detectado (db.lck). Eliminando candado para evitar errores...${NC}"
    sudo rm -f /var/lib/pacman/db.lck
fi

echo -e "${GREEN}[2/6] Inyectando repositorio privado de Omarchy...${NC}"
if ! grep -q "omarchy" /etc/pacman.conf; then
  sudo bash -c 'echo -e "\n[omarchy]\nSigLevel = Optional TrustAll\nServer = https://pkgs.omarchy.org/\$arch/\n" >> /etc/pacman.conf'
fi

echo -e "${GREEN}[3/6] Sincronizando repositorios y actualizando firmas...${NC}"
# Desactivamos exit on error momentáneamente para atrapar el fallo del keyring
set +e
if ! sudo pacman -Syu --noconfirm; then
  echo -e "${YELLOW}⚠️ Detectado problema con las firmas de CachyOS. Iniciando protocolo de autorreparación...${NC}"
  sudo rm -rf /etc/pacman.d/gnupg/
  sudo pacman-key --init
  sudo pacman-key --populate archlinux cachyos
  echo -e "${GREEN}✓ Llavero reparado. Reintentando sincronización...${NC}"
  sudo pacman -Syu --noconfirm
fi
set -e

echo -e "${GREEN}[4/6] Recopilando e instalando el núcleo de X64-Omarchy...${NC}"
# Verificamos estar en el directorio correcto
if [ ! -f "install/omarchy-base.packages" ]; then
    echo -e "${RED}Error: No se encuentran los archivos de instalación. ¿Estás ejecutando el script desde dentro de la carpeta del repositorio?${NC}"
    exit 1
fi

ALL_PACKAGES=$(cat install/omarchy-base.packages install/omarchy-other.packages | grep -v '^#' | grep -v '^$' | tr '\n' ' ')
# Desactivamos exit on error momentáneamente porque pacman -T devuelve error si faltan paquetes (lo cual es normal aquí)
set +e
MISSING_PACKAGES=$(pacman -T $ALL_PACKAGES)
set -e

if [ -n "$MISSING_PACKAGES" ]; then
  # Removemos jack2 si existe, porque entra en conflicto directo con pipewire-jack
  sudo pacman -Rdd --noconfirm jack2 2>/dev/null || true
  # Instalamos silenciosamente los que faltan
  sudo pacman -S --noconfirm $MISSING_PACKAGES
else
  echo -e "${CYAN}Todos los paquetes ya están instalados. Omitiendo descarga.${NC}"
fi

echo -e "${GREEN}[5/6] Aplicando El Escudo (Dotfiles, Sesión y Servicios)...${NC}"
mkdir -p ~/.config ~/.local/bin ~/.local/share/themes
sudo mkdir -p /usr/share/omarchy

sudo cp -r bin config default shell themes /usr/share/omarchy/ 2>/dev/null || true
sudo chmod -R 755 /usr/share/omarchy

# Registrar sesión y terminal
sudo mkdir -p /usr/share/wayland-sessions
sudo cp default/wayland-sessions/omarchy.desktop /usr/share/wayland-sessions/ 2>/dev/null || true

sudo mkdir -p /usr/share/xdg-terminal-exec
sudo cp default/xdg-terminal-exec/hyprland-xdg-terminals.list /usr/share/xdg-terminal-exec/ 2>/dev/null || true

sudo bash -c 'echo "export OMARCHY_PATH=/usr/share/omarchy" > /etc/profile.d/omarchy.sh'
sudo chmod +x /etc/profile.d/omarchy.sh

cp -r config/* ~/.config/ 2>/dev/null || true
cp -r bin/* ~/.local/bin/ 2>/dev/null || true
cp -r themes/* ~/.local/share/themes/ 2>/dev/null || true
chmod +x ~/.local/bin/* 2>/dev/null || true

# Activando Servicios Críticos
sudo systemctl enable sddm.service --now 2>/dev/null || true
sudo systemctl enable bluetooth.service 2>/dev/null || true

echo -e "${GREEN}[6/6] Inicializando Tema y Entorno (Tokyo Night)...${NC}"
export OMARCHY_PATH=/usr/share/omarchy
/usr/share/omarchy/bin/omarchy-theme-set "Tokyo Night" 2>/dev/null || true

echo -e "\n${BLUE}=======================================================${NC}"
echo -e "${GREEN}    ¡Instalación de X64-Omarchy Completada con Éxito!  ${NC}"
echo -e "${BLUE}=======================================================${NC}\n"

read -p "¿Deseas reiniciar tu sistema ahora para aplicar todos los cambios? (S/n): " answer
if [[ "$answer" =~ ^[Ss]$ ]] || [[ -z "$answer" ]]; then
    echo -e "${CYAN}Reiniciando en 3 segundos...${NC}"
    sleep 3
    sudo reboot
else
    echo -e "${CYAN}Entendido. Recuerda reiniciar más tarde para que el entorno funcione perfectamente.${NC}"
fi
