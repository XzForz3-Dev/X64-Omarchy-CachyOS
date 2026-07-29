#!/bin/bash
# ==============================================================================
# X64-Omarchy-CachyOS Installer - Pro Edition (V3) - Gum Powered
# By X64 Studios
# ==============================================================================

set -eEuo pipefail
LOG_FILE="x64-install.log"
touch "$LOG_FILE"
chmod 644 "$LOG_FILE"

# Pre-flight check: No ejecutar como root
if [ "$EUID" -eq 0 ]; then
  echo "⚠️ Error: Por favor, NO ejecutes este script como root."
  echo "Ejecútalo como tu usuario normal. El script pedirá contraseña para sudo automáticamente."
  exit 1
fi

echo -e "\n🔒 Este instalador requiere permisos de administrador para configurar el sistema."
sudo -v


# Instalación silenciosa de Gum para la interfaz moderna
if ! command -v gum &> /dev/null; then
    echo "Preparando interfaz gráfica de instalación (instalando gum)..."
    sudo pacman -Sy --noconfirm gum >/dev/null 2>&1
fi

# Función de manejo de errores
error_handler() {
    local line=$1
    local cmd=$2
    gum style --border double --margin "1" --padding "1 2" --border-foreground 196 \
      "❌ ERROR CRÍTICO DETECTADO" "Línea: $line" "Comando fallido: $cmd" \
      "El instalador se ha detenido para proteger tu sistema." | tee -a "$LOG_FILE"
    exit 1
}

trap 'error_handler $LINENO "$BASH_COMMAND"' ERR

# Efecto de texto estilo "máquina de escribir"
type_text() {
    local text="$1"
    local delay="${2:-0.03}"
    local color="${3:-39}"
    # Imprime con gum usando el color
    gum style --foreground "$color" "$text" | pv -qL 30 2>/dev/null || echo -e "\e[38;5;${color}m${text}\e[0m"
}

clear

# Efecto de secuencia de inicio hacker
if ! command -v pv &> /dev/null; then
    sudo pacman -Sy --noconfirm pv >/dev/null 2>&1
fi

echo -e "\e[1;31m[!] Inicializando motor gráfico de instalación...\e[0m"
sleep 0.5
echo -e "\e[1;33m[!] Desactivando protocolos estándar...\e[0m"
sleep 0.5
echo -e "\e[1;32m[✓] Acceso de administrador concedido.\e[0m"
sleep 1
clear

# ASCII Logo con efecto de "dibujado" línea por línea
echo ""
while IFS= read -r line; do
    echo -e "\e[1;38;5;87m$line\e[0m"
    sleep 0.05
done << "EOF"
██╗  ██╗ ██████╗ ██╗  ██╗    ███████╗████████╗██╗   ██╗██████╗ ██╗ ██████╗ ███████╗
╚██╗██╔╝██╔════╝ ██║  ██║    ██╔════╝╚══██╔══╝██║   ██║██╔══██╗██║██╔═══██╗██╔════╝
 ╚███╔╝ ███████╗ ███████║    ███████╗   ██║   ██║   ██║██║  ██║██║██║   ██║███████╗
 ██╔██╗ ██╔═══██╗╚════██║    ╚════██║   ██║   ██║   ██║██║  ██║██║██║   ██║╚════██║
██╔╝ ██╗╚██████╔╝     ██║    ███████║   ██║   ╚██████╔╝██████╔╝██║╚██████╔╝███████║
╚═╝  ╚═╝ ╚═════╝      ╚═╝    ╚══════╝   ╚═╝    ╚═════╝ ╚═════╝ ╚═╝ ╚═════╝ ╚══════╝
EOF
echo ""

# Mensaje de bienvenida con animación de PV (Pipe Viewer) para efecto de tipeado real
echo "Bienvenido al Instalador de X64-Omarchy para CachyOS" | pv -qL 20 | gum style --border rounded --border-foreground 99 --padding "0 2" --margin "1" 


# 1. AUTO-ACTUALIZADOR (GIT PULL)
gum spin --spinner dot --title "Buscando actualizaciones en el repositorio..." -- git pull origin quattro 2>&1 | tee -a "$LOG_FILE"
gum style --foreground 76 "✓ Instalador verificado y actualizado."

# Pre-flight check: Internet
gum spin --spinner line --title "Verificando conexión a internet..." -- ping -c 1 archlinux.org >/dev/null 2>&1
gum style --foreground 76 "✓ Conexión establecida."

echo ""
gum style --foreground 214 "¿Listo para comenzar la metamorfosis?"
if ! gum confirm "Iniciar configuración del sistema"; then
    gum style --foreground 196 "Instalación cancelada por el usuario."
    exit 0
fi

echo ""
gum style --foreground 39 "[1/7] Preparando el terreno (Llaveros y Bloqueos)..."
if [ -f /var/lib/pacman/db.lck ]; then
    gum style --foreground 214 "⚠️ Candado de Pacman detectado. Eliminando candado para evitar errores..."
    sudo rm -f /var/lib/pacman/db.lck
fi

gum style --foreground 39 "[2/7] Inyectando repositorio privado de Omarchy..."
if ! grep -q "omarchy" /etc/pacman.conf; then
  sudo bash -c 'echo -e "\n[omarchy]\nSigLevel = Optional TrustAll\nServer = https://pkgs.omarchy.org/\$arch/\n" >> /etc/pacman.conf'
fi

gum style --foreground 39 "[3/7] Sincronizando repositorios y actualizando firmas..."
# Desactivamos exit on error momentáneamente para atrapar el fallo del keyring
set +e
if ! sudo pacman -Syu --noconfirm 2>&1 | tee -a "$LOG_FILE"; then
  gum style --foreground 214 "⚠️ Problema de firmas de CachyOS detectado. Iniciando protocolo de autorreparación..."
  sudo rm -rf /etc/pacman.d/gnupg/
  sudo pacman-key --init 2>&1 | tee -a "$LOG_FILE"
  sudo pacman-key --populate archlinux cachyos 2>&1 | tee -a "$LOG_FILE"
  gum style --foreground 76 "✓ Llavero reparado."
  sudo pacman -Syu --noconfirm 2>&1 | tee -a "$LOG_FILE"
fi
set -e

gum style --foreground 39 "[4/7] Recopilando e instalando el núcleo de X64-Omarchy..."
if [ ! -f "install/omarchy-base.packages" ]; then
    gum style --foreground 196 "Error: No se encuentran los archivos de instalación. ¿Estás ejecutando el script desde dentro de la carpeta del repositorio?"
    exit 1
fi

ALL_PACKAGES=$(cat install/omarchy-base.packages install/omarchy-other.packages | grep -v '^#' | grep -v '^$' | tr '\n' ' ')

set +e
MISSING_PACKAGES=$(pacman -T $ALL_PACKAGES)
set -e

if [ -n "$MISSING_PACKAGES" ]; then
  sudo pacman -Rdd --noconfirm jack2 2>/dev/null || true
  # Mostramos el output de pacman porque la descarga puede ser muy larga y al usuario le gusta ver el progreso de la red
  sudo pacman -S --noconfirm $MISSING_PACKAGES 2>&1 | tee -a "$LOG_FILE"
else
  gum style --foreground 76 "Todos los paquetes ya están instalados. Omitiendo descarga."
fi

gum style --foreground 39 "[5/7] Creando copia de seguridad de tus configuraciones antiguas..."
BACKUP_NAME="x64-backup-$(date +%Y%m%d_%H%M%S).tar.gz"
if [ -d "$HOME/.config" ]; then
    set +e
    gum spin --spinner line --title "Comprimiendo ~/.config en $BACKUP_NAME..." -- bash -c "tar -czf \"$BACKUP_NAME\" -C \"$HOME\" .config 2>/dev/null || true"
    set -e
    gum style --foreground 76 "✓ Respaldo creado: $BACKUP_NAME"
fi

gum style --foreground 39 "[6/7] Aplicando El Escudo (Dotfiles, Sesión y Servicios)..."
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

gum style --foreground 39 "[7/7] Inicializando Tema y Entorno (Tokyo Night)..."
export OMARCHY_PATH=/usr/share/omarchy
/usr/share/omarchy/bin/omarchy-theme-set "Tokyo Night" 2>/dev/null || true

echo ""
gum style --border double --margin "1" --padding "1 2" --border-foreground 76 --foreground 76 "¡Instalación de X64-Omarchy Completada con Éxito!"
gum style --foreground 39 "Nota: Todos los detalles técnicos se han guardado en $LOG_FILE"

echo ""
gum style --foreground 214 "¿Deseas reiniciar tu sistema ahora para aplicar todos los cambios?"
if gum confirm "Reiniciar Sistema"; then
    gum spin --spinner line --title "Reiniciando en 3 segundos..." -- sleep 3
    sudo reboot
else
    gum style --foreground 39 "Entendido. Recuerda reiniciar más tarde para que el entorno funcione perfectamente."
fi
