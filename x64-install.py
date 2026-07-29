#!/usr/bin/env python3
# ==============================================================================
# X64-Omarchy-CachyOS Installer - Mega Dashboard (Python TUI Edition)
# By X64 Studios
# ==============================================================================

import os
import sys
import subprocess
import time
import threading
import shutil
import select
import tty
import termios
import math
from datetime import datetime
from collections import deque

try:
    from rich.live import Live
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
    from rich.layout import Layout
    from rich.align import Align
    from rich.console import Console, Group
    from rich.text import Text
    from rich.table import Table
    from rich.markup import escape
    from rich import box
except ImportError:
    print("Fatal: python-rich not found. Please run the installer via x64-install.sh")
    sys.exit(1)

try:
    import psutil
except ImportError:
    psutil = None

if os.geteuid() == 0:
    print("Por favor NO ejecutes este script como root. Ejecútalo como tu usuario normal.")
    sys.exit(1)

LOG_FILE = "x64-install.log"
console = Console()

# --- Shared State ---
log_lines = deque(maxlen=25)
install_error = None
install_done = False
start_time = None
end_time = None

current_state = "menu" # menu, working, error, done
ui_transitioned = False

error_prompt = None
error_response = None

# --- Unified Menu State ---
menu_data = [
    {
        "cat": "1. Entornos (Desktop)",
        "items": [
            {"label": "Hyprland (Tokyo Night)", "type": "toggle", "selected": True, "pkg": ["hyprland", "waybar", "swaybg", "wofi"], "desc": "Entorno base (Wayland) con estética hacker/cyberpunk, animaciones fluidas y bajo consumo de recursos."},
            {"label": "KDE Plasma 6", "type": "toggle", "selected": False, "pkg": ["plasma-meta", "konsole", "dolphin"], "desc": "Entorno moderno y altamente personalizable, con todas las herramientas nativas del ecosistema KDE."},
            {"label": "GNOME", "type": "toggle", "selected": False, "pkg": ["gnome", "gnome-extra"], "desc": "Interfaz enfocada en gestos táctiles, minimalismo y un flujo de trabajo centrado en el teclado."},
            {"label": "XFCE4", "type": "toggle", "selected": False, "pkg": ["xfce4", "xfce4-goodies"], "desc": "El entorno clásico y ultraligero por excelencia. Ideal para hardware antiguo o minimalismo extremo."},
            {"label": "Cosmic (System76)", "type": "toggle", "selected": False, "pkg": ["cosmic-session"], "desc": "El nuevo y moderno entorno de escritorio de Pop!_OS escrito en Rust (Alpha)."}
        ]
    },
    {
        "cat": "2. Navegadores Web",
        "items": [
            {"label": "Cachy Browser", "type": "toggle", "selected": True, "pkg": ["cachy-browser"], "desc": "Fork de Firefox parcheado y optimizado por el equipo de CachyOS para máximo rendimiento en este kernel."},
            {"label": "LibreWolf", "type": "toggle", "selected": False, "pkg": ["librewolf-bin"], "desc": "Versión de Firefox endurecida, enfocada al 100% en la privacidad, sin telemetría y con uBlock Origin integrado."},
            {"label": "Zen Browser", "type": "toggle", "selected": False, "pkg": ["zen-browser-bin"], "desc": "Moderno, ultra rápido, con pestañas verticales nativas y gestión optimizada de memoria (Basado en Firefox)."},
            {"label": "Brave", "type": "toggle", "selected": False, "pkg": ["brave-bin"], "desc": "Basado en Chromium, con un potente bloqueador de anuncios y rastreadores integrado a nivel de motor web."},
            {"label": "Google Chrome", "type": "toggle", "selected": False, "pkg": ["google-chrome"], "desc": "El navegador de Google. Rápido, con sincronización total del ecosistema de Google."},
            {"label": "Thorium", "type": "toggle", "selected": False, "pkg": ["thorium-browser-bin"], "desc": "El Chromium más rápido del mundo, compilado con optimizaciones AVX2 y SSE4 para CPUs modernos."}
        ]
    },
    {
        "cat": "3. Gaming y Emulación",
        "items": [
            {"label": "Steam & Proton", "type": "toggle", "selected": False, "pkg": ["steam", "protonup-qt"], "desc": "La plataforma de Valve. Incluye ProtonUp-Qt para instalar versiones personalizadas de Proton-GE."},
            {"label": "Lutris", "type": "toggle", "selected": False, "pkg": ["lutris"], "desc": "Centraliza y gestiona juegos de GOG, emuladores y scripts de Wine en una sola interfaz gráfica."},
            {"label": "Heroic Games Launcher", "type": "toggle", "selected": False, "pkg": ["heroic-games-launcher-bin"], "desc": "Cliente nativo y de código abierto para gestionar tu biblioteca de Epic Games Store y GOG en Linux."},
            {"label": "Gaming Toolkit", "type": "toggle", "selected": False, "pkg": ["mangohud", "goverlay", "gamemode", "gamescope"], "desc": "Vital para gamers: MangoHud (Telemetría en pantalla), GOverlay (GUI), GameMode (CPU) y Gamescope."},
            {"label": "Emuladores (Consolas)", "type": "toggle", "selected": False, "pkg": ["retroarch", "rpcs3-bin", "pcsx2", "dolphin-emu", "prismlauncher"], "desc": "Multi-emuladores (RetroArch), PS3 (RPCS3), PS2 (PCSX2), GameCube/Wii (Dolphin) y Minecraft (Prism)."}
        ]
    },
    {
        "cat": "4. Comunicación (Chat)",
        "items": [
            {"label": "Discord", "type": "toggle", "selected": False, "pkg": ["discord"], "desc": "El cliente oficial de Discord para chat de voz y texto."},
            {"label": "Vesktop (Discord Wayland)", "type": "toggle", "selected": False, "pkg": ["vesktop-bin"], "desc": "Cliente alternativo de Discord con soporte nativo para transmitir pantalla CON AUDIO en Wayland y Vencord integrado."},
            {"label": "Telegram Desktop", "type": "toggle", "selected": False, "pkg": ["telegram-desktop"], "desc": "Cliente oficial rápido, ligero e independiente de tu teléfono móvil."},
            {"label": "Signal Desktop", "type": "toggle", "selected": False, "pkg": ["signal-desktop"], "desc": "El estándar de oro en mensajería cifrada de extremo a extremo."}
        ]
    },
    {
        "cat": "5. Multimedia y Gráficos",
        "items": [
            {"label": "Reproductores (VLC / MPV)", "type": "toggle", "selected": False, "pkg": ["vlc", "mpv"], "desc": "Reproductores universales. VLC para todo formato, y MPV para reproducción ultraligera acelerada por hardware."},
            {"label": "Spotify", "type": "toggle", "selected": False, "pkg": ["spotify"], "desc": "Cliente oficial para streaming de música y podcasts."},
            {"label": "Producción A/V (OBS / Kdenlive)", "type": "toggle", "selected": False, "pkg": ["obs-studio", "kdenlive", "audacity"], "desc": "OBS para streaming, Kdenlive para edición de video profesional, y Audacity para pistas de audio."},
            {"label": "Diseño y CGI (Krita / Blender)", "type": "toggle", "selected": False, "pkg": ["krita", "gimp", "blender", "inkscape"], "desc": "Krita (Pintura), GIMP (Retoque fotográfico), Blender (Modelado 3D) e Inkscape (Vectores)."}
        ]
    },
    {
        "cat": "6. Desarrollo (Dev)",
        "items": [
            {"label": "IDEs (VSCode / VSCodium)", "type": "toggle", "selected": False, "pkg": ["code", "vscodium-bin"], "desc": "El entorno de desarrollo de Microsoft (OSS) y su versión Codium totalmente libre de telemetría."},
            {"label": "Editores Ligeros (Neovim / Zed)", "type": "toggle", "selected": False, "pkg": ["neovim", "zed", "sublime-text-4"], "desc": "Neovim para los maestros del terminal, Zed para máxima velocidad (Rust), y Sublime Text 4."},
            {"label": "Contenedores (Docker)", "type": "toggle", "selected": False, "pkg": ["docker", "docker-compose", "podman"], "desc": "Plataformas de virtualización a nivel de sistema operativo para desplegar microservicios."},
            {"label": "Git & GitHub CLI", "type": "toggle", "selected": True, "pkg": ["git", "github-cli"], "desc": "Control de versiones esencial para clonar repositorios y compilar paquetes AUR."}
        ]
    },
    {
        "cat": "7. Ofimática",
        "items": [
            {"label": "LibreOffice", "type": "toggle", "selected": False, "pkg": ["libreoffice-fresh"], "desc": "La suite libre más potente. Alternativa completa a Microsoft Office con excelente compatibilidad."},
            {"label": "OnlyOffice / WPS Office", "type": "toggle", "selected": False, "pkg": ["onlyoffice-bin", "wps-office"], "desc": "Suites alternativas con una interfaz 'Ribbon' que clona casi perfectamente el formato DOCX/XLSX."},
            {"label": "Productividad (Obsidian / Mail)", "type": "toggle", "selected": False, "pkg": ["obsidian", "thunderbird", "okular"], "desc": "Gestión de conocimiento con Obsidian, correo con Thunderbird y el potente lector de PDF Okular."}
        ]
    },
    {
        "cat": "8. Sistema y Compresión",
        "items": [
            {"label": "Utilidades Base (Vital)", "type": "toggle", "selected": True, "pkg": ["base-devel", "p7zip", "unrar", "unzip", "ntfs-3g"], "desc": "[CRÍTICO] Instala compiladores básicos, soporte para ZIP/RAR/7Z y drivers para montar USBs formateados en Windows (NTFS)."},
            {"label": "Respaldo (Timeshift)", "type": "toggle", "selected": True, "pkg": ["timeshift"], "desc": "Permite crear 'Snapshots' del sistema. Si algo se rompe tras una actualización, puedes restaurar tu PC en 2 segundos."},
            {"label": "Monitoreo (Btop / Fastfetch)", "type": "toggle", "selected": True, "pkg": ["btop", "fastfetch", "stacer"], "desc": "Visualiza el consumo de CPU/RAM (Btop), tu hardware (Fastfetch) y optimiza el sistema gráfico (Stacer)."},
            {"label": "Discos (GParted)", "type": "toggle", "selected": False, "pkg": ["gparted", "partitionmanager"], "desc": "Gestores gráficos de particiones y unidades de almacenamiento. Formatea o redimensiona discos fácilmente."}
        ]
    },
    {
        "cat": "9. Archivos y Terminales",
        "items": [
            {"label": "Terminales Gráficas (Alacritty / Kitty)", "type": "toggle", "selected": True, "pkg": ["alacritty", "kitty", "wezterm", "foot"], "desc": "Terminales aceleradas por GPU para máximo rendimiento sin uso de CPU. Alacritty viene por defecto."},
            {"label": "Gestores de Archivos Gráficos", "type": "toggle", "selected": False, "pkg": ["thunar", "dolphin", "nautilus"], "desc": "Navegación tradicional de archivos y carpetas usando una interfaz visual intuitiva."},
            {"label": "Gestores de Archivos CLI (Yazi)", "type": "toggle", "selected": False, "pkg": ["yazi", "ranger", "mc"], "desc": "Navegación de archivos ultrarrápida directamente desde la terminal con previsualización de imágenes."}
        ]
    },
    {
        "cat": "10. Shells, Fuentes e Impresión",
        "items": [
            {"label": "Intérpretes (Zsh / Fish)", "type": "toggle", "selected": True, "pkg": ["zsh", "fish"], "desc": "Reemplaza al antiguo bash. Ofrecen autocompletado inteligente basado en tu historial y syntax highlighting."},
            {"label": "Nerd Fonts y Emojis", "type": "toggle", "selected": True, "pkg": ["ttf-fira-code", "ttf-meslo-nerd", "noto-fonts-emoji"], "desc": "[ESENCIAL] Evita que los íconos de la terminal, Waybar o VSCode se vean como cuadrados rotos."},
            {"label": "Impresión (CUPS)", "type": "toggle", "selected": False, "pkg": ["cups", "cups-pdf", "system-config-printer"], "desc": "Habilita los demonios de impresión para reconocer impresoras físicas y generar archivos PDF."}
        ]
    },
    {
        "cat": "11. Audio y Redes",
        "items": [
            {"label": "Audio (PipeWire)", "type": "toggle", "selected": True, "pkg": ["pipewire", "pipewire-pulse", "pipewire-alsa", "pipewire-jack", "wireplumber", "easyeffects"], "desc": "Servidor de audio de baja latencia con el ecualizador avanzado EasyEffects para mejorar tu micrófono y audífonos."},
            {"label": "Bluetooth (Bluez)", "type": "toggle", "selected": True, "pkg": ["bluez", "bluez-utils", "blueman"], "desc": "Pila oficial de Bluetooth. Necesaria para conectar audífonos inalámbricos y mandos de consola (Xbox/PlayStation)."},
            {"label": "Red y Seguridad", "type": "toggle", "selected": False, "pkg": ["ufw", "tailscale", "wireguard-tools", "dnscrypt-proxy"], "desc": "Firewall fácil (UFW), redes P2P cifradas (Tailscale/Wireguard) y encriptación de DNS (DNSCrypt)."}
        ]
    },
    {
        "cat": "12. VMs, Nube y Torrents",
        "items": [
            {"label": "Máquinas Virtuales (QEMU/KVM)", "type": "toggle", "selected": False, "pkg": ["virt-manager", "qemu-desktop", "gnome-boxes", "virtualbox"], "desc": "Instala hipervisores potentes para emular Windows u otras distribuciones con rendimiento casi nativo."},
            {"label": "Gestores de Contraseñas", "type": "toggle", "selected": False, "pkg": ["bitwarden", "keepassxc"], "desc": "Almacena tus credenciales cifradas con estándares de grado militar y autocompletado en navegadores."},
            {"label": "Sincronización (Nube)", "type": "toggle", "selected": False, "pkg": ["syncthing", "nextcloud-client"], "desc": "Herramientas de sincronización descentralizada (P2P) para mantener carpetas idénticas entre PC y celular."},
            {"label": "Descargas P2P (Torrents)", "type": "toggle", "selected": False, "pkg": ["qbittorrent", "jdownloader2", "transmission-gtk"], "desc": "Gestores robustos para descargar archivos torrent de forma segura y automatizar descargas de enlaces directos."}
        ]
    },
    {
        "cat": "13. Drivers Gráficos",
        "items": [
            {"label": "Mesa (AMD / Intel)", "type": "toggle", "selected": True, "pkg": ["mesa", "lib32-mesa", "vulkan-radeon", "lib32-vulkan-radeon", "vulkan-intel", "lib32-vulkan-intel"], "desc": "Drivers de código abierto para gráficas Radeon e Intel. Rendimiento nativo sobresaliente en Wayland para gaming."},
            {"label": "NVIDIA (Privativo DKMS)", "type": "toggle", "selected": False, "pkg": ["nvidia-dkms", "nvidia-utils", "lib32-nvidia-utils", "nvidia-settings"], "desc": "Módulo DKMS y bibliotecas propietarias de NVIDIA. Esencial para extraer el 100% del rendimiento en tarjetas RTX y GTX."}
        ]
    },
    {
        "cat": "14. Acción Final",
        "items": [
            {"label": "[ INICIAR METAMORFOSIS ]", "type": "action", "selected": False, "pkg": [], "desc": "Inicia la secuencia de instalación automatizada. Procesará todas las dependencias seleccionadas y configurará los servicios del sistema permanentemente."}
        ]
    }
]
active_pane = "left"
cat_idx = 0
item_idx = 0
user_choices = {"theme": "Tokyo Night", "drivers": "Mesa (AMD/Intel)", "packages": []}
transition_text = ""

def log(msg):
    time_str = datetime.now().strftime('%H:%M:%S')
    with open(LOG_FILE, "a") as f:
        f.write(f"[{time_str}] {msg}\n")
    log_lines.append(f"[bold blue][{time_str}][/bold blue] [bold cyan]{msg}[/bold cyan]")

def gum_choose(title, options):
    os.system("clear")
    print(f"\n\033[1;36m=== {title} ===\033[0m\n")
    print("\033[1;33mInstrucciones:\033[0m Usa las FLECHAS para moverte y ENTER para confirmar.\n")
    cmd = ["gum", "choose"]
    cmd.extend(options)
    res = subprocess.run(cmd, stdout=subprocess.PIPE, text=True)
    return [x for x in res.stdout.strip().split('\n') if x]

def run_cmd_live(cmd, check=True):
    global error_prompt, error_response, current_state
    
    while True:
        log(f"Ejecutando: {cmd}")
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        
        with open(LOG_FILE, "a") as f:
            for line in process.stdout:
                line_clean = line.strip()
                if line_clean:
                    f.write(line)
                    safe_line = escape(line_clean)
                    log_lines.append(f"[dim white]{safe_line}[/dim white]")
                    
        process.wait()
        
        if check and process.returncode != 0:
            log(f"FALLO: El comando devolvió código {process.returncode}")
            current_state = "error"
            error_prompt = {"msg": f"El comando falló con código {process.returncode}:\n{cmd}"}
            
            while error_response is None:
                time.sleep(0.1)
                
            resp = error_response
            error_response = None
            current_state = "working"
            
            if resp == "Reintentar":
                log(f"Reintentando comando: {cmd}")
                continue
            elif resp == "Ignorar":
                log(f"Ignorando error y continuando: {cmd}")
                return process.returncode
            else:
                raise Exception(f"Abortado por el usuario tras fallo en: {cmd}")
                
        return process.returncode

# --- System Info (Panel Izquierdo: Fastfetch + Live) ---
def get_sys_info():
    table = Table(show_header=False, expand=True, box=None)
    
    ff_text = ""
    try:
        res = subprocess.run(["fastfetch", "--logo", "none"], stdout=subprocess.PIPE, text=True)
        if res.returncode == 0:
            ff_text = res.stdout.strip()
    except:
        pass
        
    if not ff_text:
        ff_text = "Detección de Hardware fallida (Fastfetch no disponible)."
        
    table.add_row(Text.from_ansi(ff_text))
    table.add_row("")
    
    cpu_percent = psutil.cpu_percent() if psutil else 0
    ram = psutil.virtual_memory() if psutil else None
    ram_percent = ram.percent if ram else 0
    
    bar_len = 25
    cpu_filled = int((cpu_percent / 100) * bar_len)
    cpu_bar = "█" * cpu_filled + "░" * (bar_len - cpu_filled)
    
    ram_filled = int((ram_percent / 100) * bar_len)
    ram_bar = "█" * ram_filled + "░" * (bar_len - ram_filled)
    
    table.add_row(f"[cyan]CPU Uso:[/cyan] [yellow]{cpu_percent:>5.1f}%[/yellow] [green]{cpu_bar}[/green]")
    table.add_row(f"[cyan]RAM Uso:[/cyan] [yellow]{ram_percent:>5.1f}%[/yellow] [magenta]{ram_bar}[/magenta]")
    
    return table

# --- Layout Setup ---
layout = Layout()
layout.split_row(
    Layout(name="left", ratio=1),
    Layout(name="right", ratio=2)
)

layout["left"].split_column(
    Layout(name="logo", ratio=1),
    Layout(name="sysinfo", ratio=1)
)

logo_text = """
██╗  ██╗ ██████╗ ██╗  ██╗
╚██╗██╔╝██╔════╝ ██║  ██║
 ╚███╔╝ ███████╗ ███████║
 ██╔██╗ ██╔═══██╗╚════██║
██╔╝ ██╗╚██████╔╝     ██║
╚═╝  ╚═╝ ╚═════╝      ╚═╝
   [ X64 STUDIOS ]
"""

qr_text = """
█████████████████████████████████████
██ ▄▄▄▄▄ ██▄▄▄█  ▀  ▄█▄ █▄██ ▄▄▄▄▄ ██
██ █   █ █ ▀▀██▄▀  ▄▄ ▀▄ █▀█ █   █ ██
██ █▄▄▄█ █  ▀▀▀▀▀ ▀▀▄█▀▄█▄██ █▄▄▄█ ██
██▄▄▄▄▄▄▄█ ▀ ▀▄█▄▀▄█ █▄▀▄▀ █▄▄▄▄▄▄▄██
██ ▀▄  ▄▄▀█▀▀▀█▄█▄▀▄▀▀ ▀█▀██  ▄  ▀▀██
██▀▄ ▀▄█▄█▄▀▄  █▀ ▀█▄██▀▀█ █▀█ ▀ █▀██
██▀▄  ██▄▀█▄ ▄▀█▀ ▀▀▄▄▀█▄▄▄▄▀█▄ ▀ ▀██
██ ▀▀▄▄█▄▀█▄▀▀▄█▄█▀▄█ ▀▀▄██  ▀██ ▄███
██▀▀▀▄█▄▄▀▀ ▄██▀█▀▀ █▄ █▄ ▄▄▀ ▄▀▀▀ ██
██▄ ▄█ ▀▄█▀ ▄▄██    ▀▀  ██▄▀▀  ▀ ████
██  ▄█ ▄▄ ▄▄ █▀▀▀▀▄█▀▄█▀ ▀ ▄▀▄▄ ██ ██
██ █▀▀▀ ▄▀████ █  ▄▄ ▀▄▀▀█▀ ▀█▀  ▄▀██
██▄█▄██▄▄▄▀▀▀ ▀▀ ▄█▄█▀██▄  ▄▄▄ █ ▀███
██ ▄▄▄▄▄ █▀  ▄▄█▀▄▄█▄█  ▀  █▄█ ▀  ▀██
██ █   █ █ █▀ ▀ ▄ ▀▀▄▄ ▄▄▀  ▄▄  █  ██
██ █▄▄▄█ █▄ ▀█▄█ █▀▄ ▀ ▀ ▀██ ▄▀ ▀████
██▄▄▄▄▄▄▄█▄▄▄▄▄█▄█▄▄▄▄██▄▄▄██▄███▄███
▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀
"""

def get_static_logo():
    # Añadimos un par de saltos de línea al principio para separarlo del borde superior
    t1 = Text("\n\n" + logo_text.strip('\n') + "\n", style="bold cyan", justify="center")
    t2 = Text("GITHUB REPOSITORY\n", style="bold white", justify="center")
    
    clean_qr = qr_text.strip('\n').replace('\xa0', ' ')
    t3 = Text(clean_qr, style="white", justify="center")
    
    t1.append(t2)
    t1.append(t3)
    return t1

progress = Progress(
    SpinnerColumn(),
    TextColumn("[progress.description]{task.description}"),
    BarColumn(),
    TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
)
t_health = progress.add_task("[white]Health Check del Sistema...", total=100)
t_repo = progress.add_task("[white]Preparando Repositorios...", total=100)
t_sync = progress.add_task("[white]Sincronizando Sistema...", total=100)
t_pkg = progress.add_task("[white]Instalando X64-Omarchy...", total=100)
t_backup = progress.add_task("[white]Creando Respaldo...", total=100)
t_config = progress.add_task("[white]Aplicando Configuración...", total=100)

def update_ui():
    global ui_transitioned
    border_color = "cyan"
    if current_state == "error":
        border_color = "red"
    elif current_state == "done":
        border_color = "green"
    elif current_state == "menu":
        border_color = "magenta"
    elif current_state == "transition":
        border_color = "yellow"

    static_logo = get_static_logo()
    layout["left"]["logo"].update(
        Panel(
            Align.center(static_logo),
            title="[bold white] X64 SYSTEM CORE [/bold white]",
            border_style=border_color,
            box=box.SQUARE
        )
    )
    
    layout["left"]["sysinfo"].update(
        Panel(
            get_sys_info(), 
            title="[bold blue]Hardware & Setup (Fastfetch)[/bold blue]", 
            border_style="blue",
            box=box.ROUNDED
        )
    )
    
    if current_state == "menu":
        menu_table = Table(box=None, expand=True, show_header=False, padding=(0, 1))
        menu_table.add_column("Categorías", ratio=30)
        menu_table.add_column("Opciones", ratio=70)
        
        cat_text = ""
        for i, c in enumerate(menu_data):
            if i == cat_idx:
                style = "bold cyan reverse" if active_pane == "left" else "bold cyan"
                prefix = "▶ " if active_pane == "left" else "  "
                cat_text += f"{prefix}[{style}]{c['cat']}[/{style}]\n\n"
            else:
                style = "dim white" if active_pane == "right" else "white"
                cat_text += f"  [{style}]{c['cat']}[/{style}]\n\n"
                
        item_text = ""
        items = menu_data[cat_idx]["items"]
        for i, item in enumerate(items):
            is_active = (i == item_idx and active_pane == "right")
            cursor = "[bold yellow]➤[/bold yellow] " if is_active else "  "
            
            if item["type"] == "action":
                style = "bold green reverse" if is_active else "bold green"
                item_text += f"\n{cursor}[{style}]{item['label']}[/{style}]\n"
            else:
                chk_box = "[bold green][████] ON [/bold green]" if item.get("selected", False) else "[bold bright_black][░░░░] OFF[/bold bright_black]"
                if is_active:
                    style = "bold white"
                else:
                    style = "dim white"
                    chk_box = chk_box.replace("bold", "dim")
                    
                item_text += f"{cursor}{chk_box} [{style}]{item['label']}[/{style}]\n"
                
        menu_table.add_row(cat_text, item_text)
        
        panel_content = Group(
            Text.from_markup("\n[bold cyan]NAVEGACIÓN 2D:[/bold cyan] Flechas [bold yellow]⬅️ ➡️[/bold yellow] cambian panel. Flechas [bold yellow]⬆️ ⬇️[/bold yellow] mueven selector. [bold yellow]ESPACIO[/bold yellow] alterna.\n"),
            menu_table
        )
        
        current_item = items[item_idx] if active_pane == "right" else menu_data[cat_idx]["items"][0]
        desc = current_item.get("desc", "")
        desc_text = Text(desc, style="white", justify="left")
        hud_panel = Panel(desc_text, title="[bold cyan]INFORMACIÓN DETALLADA[/bold cyan]", border_style="magenta", height=7, box=box.ROUNDED)
        
        main_layout = Layout()
        main_layout.split_column(
            Layout(Panel(panel_content, title="[bold magenta]Configuración Pre-Vuelo[/bold magenta]", border_style=border_color), ratio=1),
            Layout(hud_panel, size=7)
        )
        layout["right"].update(main_layout)
    elif current_state == "transition":
        layout["right"].update(Panel(Align.center(f"\n\n\n\n\n\n[bold yellow]{transition_text}[/bold yellow]"), title="[bold yellow]Inicializando Sistema...[/bold yellow]", border_style="yellow"))
    else:
        if not ui_transitioned:
            layout["right"].split_column(
                Layout(name="progress", ratio=1),
                Layout(name="matrix", ratio=2)
            )
            ui_transitioned = True
            
        layout["right"]["progress"].update(Panel(progress, title=f"[bold {border_color}]Progreso de Metamorfosis[/bold {border_color}]", border_style=border_color))
        matrix_text = "\n".join(log_lines)
        layout["right"]["matrix"].update(Panel(Text.from_markup(matrix_text, markup=False) if False else matrix_text, title="[bold yellow]The Matrix (Live Log)[/bold yellow]", border_style="yellow"))
        
    return layout

# --- Threads ---
def keyboard_worker():
    global current_state, active_pane, cat_idx, item_idx, user_choices, install_error, install_done
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)
        while current_state == "menu":
            if select.select([sys.stdin], [], [], 0.1)[0]:
                ch = sys.stdin.read(1)
                if ch == '\x1b':
                    ch += sys.stdin.read(2)
                
                if ch == '\x1b[A': # Arriba
                    if active_pane == "left":
                        cat_idx = max(0, cat_idx - 1)
                        item_idx = 0
                    else:
                        item_idx = max(0, item_idx - 1)
                elif ch == '\x1b[B': # Abajo
                    if active_pane == "left":
                        cat_idx = min(len(menu_data) - 1, cat_idx + 1)
                        item_idx = 0
                    else:
                        item_idx = min(len(menu_data[cat_idx]["items"]) - 1, item_idx + 1)
                elif ch == '\x1b[C': # Derecha
                    active_pane = "right"
                elif ch == '\x1b[D': # Izquierda
                    active_pane = "left"
                elif ch == ' ':
                    if active_pane == "right":
                        item = menu_data[cat_idx]["items"][item_idx]
                        if item["type"] != "action":
                            item["selected"] = not item.get("selected", False)
                elif ch == '\r' or ch == '\n':
                    if active_pane == "right":
                        item = menu_data[cat_idx]["items"][item_idx]
                        if item["type"] == "action":
                            # Procesar selecciones de menu_data
                            for c in menu_data:
                                for i in c["items"]:
                                    if i.get("selected"):
                                        user_choices["packages"].extend(i.get("pkg", []))
                                        if "NVIDIA" in i["label"]:
                                            user_choices["drivers"] = "NVIDIA (Privativo)"
                                            
                            if "NVIDIA" not in user_choices["drivers"]:
                                user_choices["packages"].extend(["mesa", "lib32-mesa", "vulkan-radeon", "lib32-vulkan-radeon", "vulkan-intel", "lib32-vulkan-intel"])
                            
                            current_state = "transition"
                            break
                        else:
                            item["selected"] = not item.get("selected", False)
                    else:
                        # Si da enter en la izquierda, se pasa a la derecha
                        active_pane = "right"
                elif ch == '\x03': # Ctrl+C
                    install_error = "Instalación abortada por el usuario (Ctrl+C)."
                    install_done = True
                    break
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        
    if current_state == "transition":
        global transition_text
        transition_text = "Cargando Secuencia de Lanzamiento..."
        time.sleep(0.7)
        transition_text = "Verificando Sistemas Vitales..."
        time.sleep(0.7)
        transition_text = "Desplegando Motor X64-Omarchy..."
        time.sleep(0.8)
        current_state = "working"

def installer_worker():
    global install_error, install_done, current_state
    try:
        progress.update(t_health, description="[yellow]Verificando Red...", advance=30)
        run_cmd_live("ping -c 1 archlinux.org")
        progress.update(t_health, description="[yellow]Verificando Espacio en Disco...", advance=30)
        free_space = shutil.disk_usage("/").free
        if free_space < 15 * 1024 * 1024 * 1024:
            raise Exception("Espacio insuficiente. Se requieren al menos 15GB libres en /.")
        progress.update(t_health, description="[green]Sistema en Óptimas Condiciones", completed=100)
        
        progress.update(t_repo, description="[yellow]Desbloqueando Pacman...", advance=30)
        if os.path.exists("/var/lib/pacman/db.lck"):
            run_cmd_live("sudo rm -f /var/lib/pacman/db.lck")
        
        progress.update(t_repo, description="[yellow]Inyectando repo Omarchy...", advance=50)
        run_cmd_live("sudo bash -c 'grep -q \"omarchy\" /etc/pacman.conf || echo -e \"\\n[omarchy]\\nSigLevel = Optional TrustAll\\nServer = https://pkgs.omarchy.org/\\$arch/\\n\" >> /etc/pacman.conf'")
        progress.update(t_repo, description="[green]Repositorio Listo", completed=100)

        progress.update(t_sync, description="[yellow]Sincronizando firmas (Puede tardar)...", advance=20)
        res = run_cmd_live("sudo pacman -Syu --noconfirm", check=False)
        if res != 0:
            log_lines.append("[bold red]Fallo detectado. Reparando Llavero GPG...[/bold red]")
            run_cmd_live("sudo rm -rf /etc/pacman.d/gnupg/")
            progress.update(t_sync, description="[yellow]Reparando Llavero...", advance=10)
            run_cmd_live("sudo pacman-key --init")
            run_cmd_live("sudo pacman-key --populate archlinux cachyos")
            progress.update(t_sync, description="[yellow]Reintentando Sincronización...", advance=20)
            run_cmd_live("sudo pacman -Syu --noconfirm")
        progress.update(t_sync, description="[green]Sistema Sincronizado", completed=100)

        progress.update(t_pkg, description="[yellow]Calculando paquetes base...", advance=20)
        pkgs = []
        if os.path.exists("install/omarchy-base.packages"):
            with open("install/omarchy-base.packages") as f1:
                pkgs.extend(f1.read().splitlines())
        if os.path.exists("install/omarchy-other.packages"):
            with open("install/omarchy-other.packages") as f2:
                pkgs.extend(f2.read().splitlines())
        
        pkgs.extend(user_choices["packages"])
        pkg_str = " ".join([p for p in pkgs if p and not p.startswith('#')])
        
        chk = subprocess.run(f"pacman -T {pkg_str}", shell=True, stdout=subprocess.PIPE, text=True)
        if chk.returncode != 0:
            missing = chk.stdout.replace('\n', ' ').strip()
            progress.update(t_pkg, description="[cyan]Descargando e Instalando...", advance=40)
            run_cmd_live("sudo pacman -Rdd --noconfirm jack2", check=False)
            run_cmd_live(f"sudo pacman -S --noconfirm {missing}")
        progress.update(t_pkg, description="[green]Paquetes Instalados", completed=100)

        progress.update(t_backup, description="[yellow]Comprimiendo ~/.config...", advance=50)
        home = os.path.expanduser("~")
        backup_name = f"x64-backup-{datetime.now().strftime('%Y%m%d_%H%M%S')}.tar.gz"
        run_cmd_live(f"tar -czf {backup_name} -C {home} .config", check=False)
        progress.update(t_backup, description="[green]Respaldo Completado", completed=100)

        progress.update(t_config, description="[yellow]Desplegando escudo de sistema...", advance=20)
        run_cmd_live("mkdir -p ~/.config ~/.local/bin ~/.local/share/themes")
        run_cmd_live("sudo mkdir -p /usr/share/omarchy")
        run_cmd_live("sudo cp -r --remove-destination bin config default shell themes /usr/share/omarchy/ 2>/dev/null", check=False)
        run_cmd_live("sudo chmod -R 755 /usr/share/omarchy")
        
        run_cmd_live("sudo mkdir -p /usr/share/wayland-sessions")
        run_cmd_live("sudo cp default/wayland-sessions/omarchy.desktop /usr/share/wayland-sessions/", check=False)
        run_cmd_live("sudo mkdir -p /usr/share/xdg-terminal-exec")
        run_cmd_live("sudo cp default/xdg-terminal-exec/hyprland-xdg-terminals.list /usr/share/xdg-terminal-exec/", check=False)
        
        run_cmd_live("sudo bash -c 'echo \"export OMARCHY_PATH=/usr/share/omarchy\" > /etc/profile.d/omarchy.sh'")
        run_cmd_live("sudo chmod +x /etc/profile.d/omarchy.sh")
        run_cmd_live("cp -r --remove-destination config/* ~/.config/ 2>/dev/null", check=False)
        run_cmd_live("cp -r --remove-destination bin/* ~/.local/bin/ 2>/dev/null", check=False)
        run_cmd_live("cp -r --remove-destination themes/* ~/.local/share/themes/ 2>/dev/null", check=False)
        run_cmd_live("chmod +x ~/.local/bin/*", check=False)
        
        progress.update(t_config, description="[yellow]Habilitando servicios...", advance=20)
        run_cmd_live("sudo systemctl enable sddm.service --now", check=False)
        run_cmd_live("sudo systemctl enable bluetooth.service", check=False)
        if "ananicy-cpp" in user_choices["packages"]:
            run_cmd_live("sudo systemctl enable ananicy-cpp.service", check=False)
        if "zram-generator" in user_choices["packages"]:
            run_cmd_live("sudo systemctl daemon-reload", check=False)
            run_cmd_live("sudo systemctl restart systemd-zram-setup@zram0.service", check=False)
        if "uksmd" in user_choices["packages"]:
            run_cmd_live("sudo systemctl enable uksmd.service", check=False)
        if "irqbalance" in user_choices["packages"]:
            run_cmd_live("sudo systemctl enable irqbalance.service", check=False)
        if "cups" in user_choices["packages"]:
            run_cmd_live("sudo systemctl enable cups.service", check=False)
        
        progress.update(t_config, description="[yellow]Aplicando Diseño y Tema...", advance=20)
        if user_choices["theme"] == "Tokyo Night":
            run_cmd_live("export OMARCHY_PATH=/usr/share/omarchy && /usr/share/omarchy/bin/omarchy-theme-set 'Tokyo Night'", check=False)
        
        progress.update(t_config, description="[green]Sistema Listo", completed=100)
    except Exception as e:
        install_error = str(e)
    finally:
        install_done = True
        current_state = "error" if install_error else "done"

# --- Launch Sequence ---
with open(LOG_FILE, "w") as f:
    f.write("=== Inicio de Instalación X64-Omarchy (Mega Dashboard) ===\n")

k_worker = threading.Thread(target=keyboard_worker, daemon=True)
k_worker.start()

try:
    with Live(update_ui(), refresh_per_second=10, screen=True) as live:
        while not install_done:
            time.sleep(0.1)
            
            if current_state == "error" and error_prompt:
                live.stop()
                os.system("clear")
                print(f"\n\033[1;41m[ ATENCIÓN - ERROR CRÍTICO ]\033[0m")
                print(f"\033[1;33m{error_prompt['msg']}\033[0m\n")
                ans = gum_choose("¿Cómo deseas proceder?", ["Reintentar", "Ignorar", "Abortar"])
                error_response = ans[0] if ans else "Abortar"
                error_prompt = None
                os.system("clear")
                live.start()
            elif current_state == "working" and not start_time:
                start_time = time.time()
                worker = threading.Thread(target=installer_worker, daemon=True)
                worker.start()
                
            live.update(update_ui())
                
        end_time = time.time()
        live.update(update_ui())
        time.sleep(2)
except KeyboardInterrupt:
    install_error = "Instalación abortada por el usuario (Ctrl+C)."
    install_done = True

print("\n")
if not install_error:
    time_taken = end_time - start_time if start_time else 0
    mins, secs = divmod(time_taken, 60)
    
    report = Table(title="[bold cyan]Reporte Final de Metamorfosis X64[/bold cyan]", box=None, expand=True)
    report.add_column("Métrica", style="cyan")
    report.add_column("Detalle", style="white")
    
    report.add_row("Tiempo de Instalación", f"{int(mins)}m {int(secs)}s")
    report.add_row("Tema Base", user_choices["theme"])
    report.add_row("Drivers Instalados", user_choices["drivers"])
    report.add_row("Software Extra Elegido", f"{len(user_choices['packages'])} paquetes")
    if len(user_choices["packages"]) > 0:
        report.add_row("Lista de Software", ", ".join(user_choices["packages"]))
    report.add_row("Archivo de Log", f"[dim]{LOG_FILE}[/dim]")
    
    console.print(Panel(report, border_style="green", title="[bold green]¡Sistema Listo![/bold green]"))
    print("\n[!] Por favor, reinicia tu computadora para aplicar los cambios.\n")
else:
    console.print(Panel(f"[bold red]La instalación fue abortada: {install_error}[/bold red]", expand=False))
