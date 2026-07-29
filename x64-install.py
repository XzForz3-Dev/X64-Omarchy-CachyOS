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
        "cat": "1. Kernel y Base",
        "items": [
            {"label": "Kernel: CachyOS BORE", "type": "toggle", "selected": True, "pkg": ["linux-cachyos", "linux-cachyos-headers"], "desc": "Instala el núcleo de CachyOS optimizado con el planificador BORE. Garantiza máxima responsividad bajo carga pesada en entornos de escritorio."},
            {"label": "Kernel: CachyOS LTO", "type": "toggle", "selected": False, "pkg": ["linux-cachyos-lto", "linux-cachyos-lto-headers"], "desc": "Núcleo compilado con Link Time Optimization (LTO). Ofrece un mayor rendimiento a expensas de tiempos de compilación de módulos más largos."},
            {"label": "Kernel: Standard Arch", "type": "toggle", "selected": False, "pkg": ["linux", "linux-headers"], "desc": "El núcleo por defecto de Arch Linux. Seguro, vainilla y sin optimizaciones específicas de latencia."}
        ]
    },
    {
        "cat": "2. Entornos de Escritorio",
        "items": [
            {"label": "Hyprland (Tokyo Night)", "type": "toggle", "selected": True, "pkg": ["hyprland", "waybar", "swaybg", "wofi"], "desc": "Aplica el tema oscuro 'Tokyo Night' para Hyprland. Proporciona una estética hacker/cyberpunk unificada basada en Wayland."},
            {"label": "KDE Plasma", "type": "toggle", "selected": False, "pkg": ["plasma-meta", "konsole"], "desc": "Un entorno de escritorio familiar, personalizable y moderno que incluye todas las herramientas gráficas de KDE."},
            {"label": "GNOME", "type": "toggle", "selected": False, "pkg": ["gnome", "gnome-extra"], "desc": "Entorno moderno y minimalista, enfocado en flujos de trabajo basados en teclado y gestos táctiles fluidos."}
        ]
    },
    {
        "cat": "3. Terminales",
        "items": [
            {"label": "Alacritty (GPU-Accelerated)", "type": "toggle", "selected": True, "pkg": ["alacritty"], "desc": "Emulador de terminal hiper-rápido, renderizado por GPU mediante OpenGL. Configurado con el tema Tokyo Night por defecto."},
            {"label": "Kitty", "type": "toggle", "selected": False, "pkg": ["kitty"], "desc": "Terminal acelerada por hardware con soporte nativo para visualización de imágenes (Kitten) y multiplexación integrada."},
            {"label": "WezTerm", "type": "toggle", "selected": False, "pkg": ["wezterm"], "desc": "Terminal hiper-configurable en Lua, con multiplexador nativo, aceleración de GPU y gran soporte de fuentes con ligaduras."}
        ]
    },
    {
        "cat": "4. Rendimiento y Tweaks",
        "items": [
            {"label": "Tweak: Ananicy-cpp", "type": "toggle", "selected": True, "pkg": ["ananicy-cpp"], "desc": "Demonio auto-nice. Asigna prioridades a procesos dinámicamente usando reglas comunitarias para garantizar que tu escritorio y juegos tengan máxima prioridad."},
            {"label": "Tweak: ZRAM (Swap en RAM)", "type": "toggle", "selected": True, "pkg": ["zram-generator"], "desc": "Configura compresión en la RAM (zstd). Evita la paginación a disco, extendiendo la vida útil del SSD y manteniendo el sistema ultra fluido."},
            {"label": "Tweak: UKSMD (Deduplicación)", "type": "toggle", "selected": False, "pkg": ["uksmd"], "desc": "Ultra KSM Daemon. Escanea la memoria en segundo plano y fusiona páginas idénticas. Libera RAM masivamente para máquinas virtuales o contenedores."},
            {"label": "Tweak: Irqbalance", "type": "toggle", "selected": True, "pkg": ["irqbalance"], "desc": "Distribuye las interrupciones de hardware a través de todos los núcleos del CPU, mejorando drásticamente el rendimiento I/O (discos, red)."},
            {"label": "Tweak: CachyOS Settings", "type": "toggle", "selected": True, "pkg": ["cachyos-settings"], "desc": "Aplica los sysctl y reglas udev recomendadas por el equipo de CachyOS para red, memoria y optimización del sistema base."}
        ]
    },
    {
        "cat": "5. Drivers Gráficos",
        "items": [
            {"label": "Mesa (AMD / Intel)", "type": "toggle", "selected": True, "pkg": ["mesa", "lib32-mesa", "vulkan-radeon", "lib32-vulkan-radeon", "vulkan-intel", "lib32-vulkan-intel"], "desc": "Drivers de código abierto para gráficas AMD Radeon e Intel. Rendimiento nativo sobresaliente en Wayland para gaming."},
            {"label": "NVIDIA (Privativo DKMS)", "type": "toggle", "selected": False, "pkg": ["nvidia-dkms", "nvidia-utils", "lib32-nvidia-utils", "nvidia-settings"], "desc": "Módulo DKMS y bibliotecas propietarias de NVIDIA. Esencial para extraer el 100% del rendimiento en tarjetas RTX y GTX."}
        ]
    },
    {
        "cat": "6. Navegadores Web",
        "items": [
            {"label": "Mozilla Firefox", "type": "toggle", "selected": True, "pkg": ["firefox"], "desc": "El navegador libre por excelencia. Optimizado para privacidad y velocidad de renderizado. Preconfigurado con aceleración en Wayland."},
            {"label": "Brave Browser", "type": "toggle", "selected": False, "pkg": ["brave-bin"], "desc": "Basado en Chromium, enfocado en extrema privacidad. Incluye un bloqueador de rastreadores muy agresivo a nivel de motor."},
            {"label": "Zen Browser", "type": "toggle", "selected": False, "pkg": ["zen-browser-bin"], "desc": "Un fork moderno y minimalista de Firefox, diseñado para pestañas verticales y uso intensivo sin saturar la RAM."},
            {"label": "Chromium", "type": "toggle", "selected": False, "pkg": ["chromium"], "desc": "La base de código abierto detrás de Google Chrome. Rápido, puro y sin telemetría intrusiva directa."}
        ]
    },
    {
        "cat": "7. Audio y Red",
        "items": [
            {"label": "Audio: PipeWire", "type": "toggle", "selected": True, "pkg": ["pipewire", "pipewire-pulse", "pipewire-alsa", "pipewire-jack", "wireplumber"], "desc": "El futuro del audio en Linux. Servidor multimedia de bajísima latencia que reemplaza a PulseAudio. Ideal para gaming sin retardo."},
            {"label": "Red: Bluetooth (Bluez)", "type": "toggle", "selected": True, "pkg": ["bluez", "bluez-utils", "blueman"], "desc": "Demonios base de Bluez y gestor Blueman. Necesario para conectar auriculares inalámbricos, mandos de consola (Xbox/PS5) e IoT."},
            {"label": "Red: DNSCrypt-Proxy", "type": "toggle", "selected": False, "pkg": ["dnscrypt-proxy"], "desc": "Herramienta que encripta tus consultas DNS hacia los servidores. Previene el rastreo y censura a nivel de proveedor de internet (ISP)."}
        ]
    },
    {
        "cat": "8. Gaming",
        "items": [
            {"label": "Steam (Runtime y Nativo)", "type": "toggle", "selected": False, "pkg": ["steam"], "desc": "La plataforma de videojuegos líder. Viene con herramientas Proton integradas para ejecutar cualquier juego de Windows en Linux."},
            {"label": "Lutris & Heroic Launcher", "type": "toggle", "selected": False, "pkg": ["lutris", "heroic-games-launcher-bin", "wine-staging"], "desc": "Lanzadores épicos. Lutris centraliza tus juegos de GOG y emuladores, y Heroic gestiona tu biblioteca de Epic Games Store nativamente."},
            {"label": "Herramientas (MangoHud/GameMode)", "type": "toggle", "selected": False, "pkg": ["mangohud", "gamemode", "gamescope"], "desc": "Telemetría OSD en pantalla (MangoHud), optimización agresiva del CPU al jugar (GameMode) y microcompositor de aislamiento (Gamescope)."}
        ]
    },
    {
        "cat": "9. Desarrollo (Dev)",
        "items": [
            {"label": "Control de Versiones (Git)", "type": "toggle", "selected": True, "pkg": ["git", "github-cli"], "desc": "Sistemas de control de código fuente estándar de la industria. Indispensable para clonar repositorios y compilar paquetes AUR."},
            {"label": "Contenedores (Docker)", "type": "toggle", "selected": False, "pkg": ["docker", "docker-compose"], "desc": "Plataforma de virtualización y contenedores nativa. Aísla tus aplicaciones en microservicios listos para producción."},
            {"label": "IDE: Visual Studio Code", "type": "toggle", "selected": False, "pkg": ["code"], "desc": "Versión Open Source de VSCode. Soporte enorme de extensiones para Python, C++, Rust, Go, y desarrollo web."}
        ]
    },
    {
        "cat": "10. Multimedia y Diseño",
        "items": [
            {"label": "Streaming: OBS Studio", "type": "toggle", "selected": False, "pkg": ["obs-studio"], "desc": "El software estándar para transmisión en vivo y grabación de pantalla. Soporta encoding NVENC y VAAPI acelerado por GPU."},
            {"label": "Diseño: Krita", "type": "toggle", "selected": False, "pkg": ["krita"], "desc": "Herramienta profesional gratuita de pintura digital e ilustración rasterizada en 2D, con soporte masivo para tabletas gráficas."},
            {"label": "Video: VLC y MPV", "type": "toggle", "selected": False, "pkg": ["vlc", "mpv"], "desc": "Reproductores universales. VLC para todo tipo de formatos sin codecs externos, y MPV para reproducción ultraligera por hardware."}
        ]
    },
    {
        "cat": "11. Ofimática e Impresión",
        "items": [
            {"label": "Suite: LibreOffice", "type": "toggle", "selected": False, "pkg": ["libreoffice-fresh"], "desc": "La suite libre más potente. Alternativa completa a Word, Excel y PowerPoint con gran compatibilidad de formatos."},
            {"label": "Impresión (CUPS)", "type": "toggle", "selected": False, "pkg": ["cups", "cups-pdf"], "desc": "Habilita el servidor Common UNIX Printing System. Actívalo si necesitas conectar impresoras físicas o imprimir documentos localmente."}
        ]
    },
    {
        "cat": "12. Iniciar Metamorfosis",
        "items": [
            {"label": "[ APLICAR Y DESPLEGAR SISTEMA ]", "type": "action", "selected": False, "pkg": [], "desc": "Inicia la secuencia de instalación automatizada. Procesará todas las dependencias seleccionadas y configurará los servicios del sistema permanentemente."}
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
