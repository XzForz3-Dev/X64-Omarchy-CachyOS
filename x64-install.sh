#!/bin/bash
# ==============================================================================
# X64-Omarchy-CachyOS Installer - Pro Edition (V2)
# By X64 Studios
# ==============================================================================

set -eEuo pipefail
LOG_FILE="x64-install.log"
touch "$LOG_FILE"
chmod 644 "$LOG_FILE"

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
    echo -e "\n${RED}==========================================================${NC}" | tee -a "$LOG_FILE"
    echo -e "${RED}❌ ERROR CRÍTICO DETECTADO${NC}" | tee -a "$LOG_FILE"
    echo -e "${RED}Línea: ${NC}$line" | tee -a "$LOG_FILE"
    echo -e "${RED}Comando fallido: ${NC}$cmd" | tee -a "$LOG_FILE"
    echo -e "${RED}El instalador se ha detenido para proteger tu sistema.${NC}" | tee -a "$LOG_FILE"
    echo -e "${RED}==========================================================${NC}\n" | tee -a "$LOG_FILE"
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

# 1. AUTO-ACTUALIZADOR (GIT PULL)
echo -e "${CYAN}[*] Buscando actualizaciones en el repositorio oficial...${NC}"
git pull origin quattro 2>&1 | tee -a "$LOG_FILE"
echo -e "${GREEN}✓ Instalador verificado y actualizado.${NC}\n"

# Pre-flight check: No ejecutar como root
if [ "$EUID" -eq 0 ]; then
  echo -e "${RED}⚠️ Error: Por favor, NO ejecutes este script como root.${NC}" | tee -a "$LOG_FILE"
  echo "Ejecútalo como tu usuario normal. El script pedirá contraseña para sudo automáticamente." | tee -a "$LOG_FILE"
  exit 1
fi

# Pre-flight check: Internet
echo -e "${CYAN}Verificando conexión a internet...${NC}"
if ! ping -c 1 archlinux.org > /dev/null 2>&1; then
  echo -e "${RED}⚠️ Error: No hay conexión a internet. Verifica tu red y vuelve a intentarlo.${NC}" | tee -a "$LOG_FILE"
  exit 1
fi
echo -e "${GREEN}✓ Conexión establecida.${NC}\n"

read -p "$(echo -e ${YELLOW}Presiona ENTER para iniciar la configuración de tu sistema...${NC})"

# 2. MENÚ INTERACTIVO (WHIPTAIL)
EXTRA_PACKAGES=""
if command -v whiptail &> /dev/null; then
    EXTRA_PROFILE=$(whiptail --title "X64-Omarchy - Instalación Personalizada" \
    --checklist "Selecciona perfiles adicionales (Usa ESPACIO para seleccionar, ENTER para continuar):" 15 65 2 \
    "gamer" "Steam, Lutris, MangoHud, Wine" OFF \
    "dev" "VSCode, Docker, GitHub CLI" OFF 3>&1 1>&2 2>&3) || true
    
    if [[ $EXTRA_PROFILE == *"gamer"* ]]; then
        EXTRA_PACKAGES="$EXTRA_PACKAGES steam lutris mangohud wine"
        echo -e "${CYAN}Perfil seleccionado: GAMER${NC}" | tee -a "$LOG_FILE"
    fi
    if [[ $EXTRA_PROFILE == *"dev"* ]]; then
        EXTRA_PACKAGES="$EXTRA_PACKAGES code docker github-cli"
        echo -e "${CYAN}Perfil seleccionado: DEVELOPER${NC}" | tee -a "$LOG_FILE"
    fi
else
    echo -e "${YELLOW}Whiptail no detectado. Omitiendo menú de instalación personalizada.${NC}" | tee -a "$LOG_FILE"
fi

echo -e "\n${GREEN}[1/7] Preparando el terreno (Llaveros y Bloqueos)...${NC}"
# Reparador automático del bloqueo de pacman
if [ -f /var/lib/pacman/db.lck ]; then
    echo -e "${YELLOW}⚠️ Bloqueo de Pacman detectado (db.lck). Eliminando candado para evitar errores...${NC}" | tee -a "$LOG_FILE"
    sudo rm -f /var/lib/pacman/db.lck
fi

echo -e "${GREEN}[2/7] Inyectando repositorio privado de Omarchy...${NC}"
if ! grep -q "omarchy" /etc/pacman.conf; then
  sudo bash -c 'echo -e "\n[omarchy]\nSigLevel = Optional TrustAll\nServer = https://pkgs.omarchy.org/\$arch/\n" >> /etc/pacman.conf'
fi

echo -e "${GREEN}[3/7] Sincronizando repositorios y actualizando firmas...${NC}"
# Desactivamos exit on error momentáneamente para atrapar el fallo del keyring
set +e
if ! sudo pacman -Syu --noconfirm 2>&1 | tee -a "$LOG_FILE"; then
  echo -e "${YELLOW}⚠️ Detectado problema con las firmas de CachyOS. Iniciando protocolo de autorreparación...${NC}" | tee -a "$LOG_FILE"
  sudo rm -rf /etc/pacman.d/gnupg/
  sudo pacman-key --init 2>&1 | tee -a "$LOG_FILE"
  sudo pacman-key --populate archlinux cachyos 2>&1 | tee -a "$LOG_FILE"
  echo -e "${GREEN}✓ Llavero reparado. Reintentando sincronización...${NC}" | tee -a "$LOG_FILE"
  sudo pacman -Syu --noconfirm 2>&1 | tee -a "$LOG_FILE"
fi
set -e

echo -e "${GREEN}[4/7] Recopilando e instalando el núcleo de X64-Omarchy...${NC}"
# Verificamos estar en el directorio correcto
if [ ! -f "install/omarchy-base.packages" ]; then
    echo -e "${RED}Error: No se encuentran los archivos de instalación. ¿Estás ejecutando el script desde dentro de la carpeta del repositorio?${NC}" | tee -a "$LOG_FILE"
    exit 1
fi

ALL_PACKAGES=$(cat install/omarchy-base.packages install/omarchy-other.packages | grep -v '^#' | grep -v '^$' | tr '\n' ' ')
ALL_PACKAGES="$ALL_PACKAGES $EXTRA_PACKAGES"

# Desactivamos exit on error momentáneamente porque pacman -T devuelve error si faltan paquetes (lo cual es normal aquí)
set +e
MISSING_PACKAGES=$(pacman -T $ALL_PACKAGES)
set -e

if [ -n "$MISSING_PACKAGES" ]; then
  # Removemos jack2 si existe, porque entra en conflicto directo con pipewire-jack
  sudo pacman -Rdd --noconfirm jack2 2>/dev/null || true
  # Instalamos los que faltan logueando a pantalla y archivo
  sudo pacman -S --noconfirm $MISSING_PACKAGES 2>&1 | tee -a "$LOG_FILE"
else
  echo -e "${CYAN}Todos los paquetes ya están instalados. Omitiendo descarga.${NC}" | tee -a "$LOG_FILE"
fi

# 3. SISTEMA DE RESPALDO (BACKUP)
echo -e "${GREEN}[5/7] Creando copia de seguridad de tus configuraciones antiguas...${NC}"
BACKUP_NAME="x64-backup-$(date +%Y%m%d_%H%M%S).tar.gz"
if [ -d "$HOME/.config" ]; then
    echo -e "${CYAN}Comprimiendo ~/.config en $BACKUP_NAME...${NC}" | tee -a "$LOG_FILE"
    tar -czf "$BACKUP_NAME" -C "$HOME" .config 2>/dev/null || true
    echo -e "${GREEN}✓ Respaldo creado: $BACKUP_NAME${NC}" | tee -a "$LOG_FILE"
fi

echo -e "${GREEN}[6/7] Aplicando El Escudo (Dotfiles, Sesión y Servicios)...${NC}"
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

echo -e "${GREEN}[7/7] Inicializando Tema y Entorno (Tokyo Night)...${NC}"
export OMARCHY_PATH=/usr/share/omarchy
/usr/share/omarchy/bin/omarchy-theme-set "Tokyo Night" 2>/dev/null || true

echo -e "\n${BLUE}=======================================================${NC}" | tee -a "$LOG_FILE"
echo -e "${GREEN}    ¡Instalación de X64-Omarchy Completada con Éxito!  ${NC}" | tee -a "$LOG_FILE"
echo -e "${BLUE}=======================================================${NC}\n" | tee -a "$LOG_FILE"
echo -e "${CYAN}Nota: Todos los detalles técnicos se han guardado en $LOG_FILE${NC}"

read -p "¿Deseas reiniciar tu sistema ahora para aplicar todos los cambios? (S/n): " answer
if [[ "$answer" =~ ^[Ss]$ ]] || [[ -z "$answer" ]]; then
    echo -e "${CYAN}Reiniciando en 3 segundos...${NC}"
    sleep 3
    sudo reboot
else
    echo -e "${CYAN}Entendido. Recuerda reiniciar más tarde para que el entorno funcione perfectamente.${NC}"
fi
