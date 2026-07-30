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
import json
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
    from rich.prompt import Prompt
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
with open("core/menu_data.json", "r", encoding="utf-8") as f:
    menu_data = json.load(f)

active_pane = "left"
cat_idx = 0
item_idx = 0
user_choices = {"theme": "Tokyo Night", "drivers": "Mesa (AMD/Intel)", "packages": []}
transition_text = ""
is_legacy_nvidia = False
has_nvidia = False

try:
    pci_out = subprocess.check_output("lspci -k | grep -iEA3 'vga|3d|display'", shell=True, text=True).lower()
    if "nvidia" in pci_out:
        has_nvidia = True
        if any(arch in pci_out for arch in ["gtx 9", "gtx 7", "gtx 6", "kepler", "maxwell"]):
             is_legacy_nvidia = True
except Exception:
    pass

# Auto-toggle drivers based on hardware detection
for c in menu_data:
    if "Drivers" in c["cat"]:
        for item in c["items"]:
            if item["label"] == "Mesa (AMD / Intel)":
                item["selected"] = not has_nvidia
            elif item["label"] == "NVIDIA (Privativo DKMS)":
                item["selected"] = has_nvidia and not is_legacy_nvidia

def log(msg):
    time_str = datetime.now().strftime('%H:%M:%S')
    with open(LOG_FILE, "a") as f:
        f.write(f"[{time_str}] {msg}\n")
    log_lines.append(f"[bold blue][{time_str}][/bold blue] [bold cyan]{msg}[/bold cyan]")

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
    
    if not hasattr(get_sys_info, "ff_text"):
        get_sys_info.ff_text = ""
        get_sys_info.last_update = 0
        get_sys_info.cached_rows = []
        try:
            res = subprocess.run(["fastfetch", "--logo", "none", "--structure", "Title:Separator:OS:Host:Kernel:Uptime:Packages:Shell:Display:WM:CPU:GPU:Memory:Swap:Disk:LocalIP:Battery:PowerAdapter:Locale:Vulkan:OpenGL"], stdout=subprocess.PIPE, text=True)
            if res.returncode == 0:
                raw_text = res.stdout.strip()
                colored_lines = []
                import re
                ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
                for line in raw_text.split('\n'):
                    clean_line = ansi_escape.sub('', line).strip()
                    if not clean_line:
                        continue
                    sep = " 󰁔 " if " 󰁔 " in line else (": " if ": " in line else None)
                    if sep:
                        key, val = line.split(sep, 1)
                        colored_lines.append(f"[bold cyan]{key}[/bold cyan]{sep}[yellow]{val}[/yellow]")
                    elif "@" in line and "---" not in line and "GHz" not in line:
                        colored_lines.append(f"[bold magenta]{line}[/bold magenta]")
                    elif "---" in line:
                        colored_lines.append(f"[dim white]{line}[/dim white]")
                    else:
                        colored_lines.append(line)
                get_sys_info.ff_text = "\n".join(colored_lines)
        except:
            pass
            
        if not get_sys_info.ff_text:
            get_sys_info.ff_text = "Detección de Hardware fallida (Fastfetch no disponible)."
            
    table.add_row(Text.from_markup(get_sys_info.ff_text))
    table.add_row("")
    
    import time
    now = time.time()
    if now - get_sys_info.last_update > 1.0:
        get_sys_info.last_update = now
        rows = []
        bar_len = 18
        
        cpu_percent = psutil.cpu_percent() if psutil else 0
        cpu_filled = max(1, int((cpu_percent / 100) * bar_len)) if cpu_percent > 0 else 0
        cpu_bar = "█" * cpu_filled + "░" * (bar_len - cpu_filled)
        rows.append(f"[cyan]CPU Uso:[/cyan] [yellow]{cpu_percent:>5.1f}%[/yellow] [green]{cpu_bar}[/green]")
        
        if psutil:
            ram = psutil.virtual_memory()
            ram_percent = ram.percent
            ram_filled = max(1, int((ram_percent / 100) * bar_len)) if ram_percent > 0 else 0
            ram_bar = "█" * ram_filled + "░" * (bar_len - ram_filled)
            rows.append(f"[cyan]RAM Uso:[/cyan] [yellow]{ram_percent:>5.1f}%[/yellow] [magenta]{ram_bar}[/magenta]")
            
            try:
                disk = psutil.disk_usage('/')
                disk_percent = disk.percent
                disk_filled = max(1, int((disk_percent / 100) * bar_len)) if disk_percent > 0 else 0
                disk_bar = "█" * disk_filled + "░" * (bar_len - disk_filled)
                rows.append(f"[cyan]SSD Uso:[/cyan] [yellow]{disk_percent:>5.1f}%[/yellow] [blue]{disk_bar}[/blue]")
            except:
                pass
                
            try:
                bat = psutil.sensors_battery()
                if bat is not None:
                    bat_percent = bat.percent
                    bat_filled = max(1, int((bat_percent / 100) * bar_len)) if bat_percent > 0 else 0
                    bat_color = "red" if bat_percent < 20 and not bat.power_plugged else "green"
                    bat_bar = "█" * bat_filled + "░" * (bar_len - bat_filled)
                    plug_icon = "🔌" if bat.power_plugged else "🔋"
                    rows.append(f"[cyan]Batería:[/cyan] [yellow]{bat_percent:>5.1f}%[/yellow] [{bat_color}]{bat_bar}[/{bat_color}] {plug_icon}")
            except:
                pass
                
        get_sys_info.cached_rows = rows
        
    for row in get_sys_info.cached_rows:
        table.add_row(row)
        
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
    from rich.console import Console
    console = Console()
    
    t1 = Text("\n\n" + logo_text.strip('\n') + "\n", style="bold cyan", justify="center")
    
    # Hide QR code on small terminals to prevent layout explosion
    if console.size.height > 50:
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
            Align.center(static_logo, vertical="middle"),
            title="[bold white] X64 SYSTEM CORE [/bold white]",
            border_style=border_color,
            box=box.SQUARE
        )
    )
    
    layout["left"]["sysinfo"].update(
        Panel(
            Align.center(get_sys_info(), vertical="middle"), 
            title="[bold blue]Hardware & Setup (Fastfetch)[/bold blue]", 
            border_style="blue",
            box=box.ROUNDED
        )
    )
    
    if current_state == "menu":
        # --- VIEWPORT ROW SCROLLING LOGIC ---
        items = menu_data[cat_idx]["items"]
        MAX_ROWS = 6
        
        current_row = item_idx // 3
        start_row = max(0, current_row - (MAX_ROWS // 2))
        end_row = start_row + MAX_ROWS
        
        total_rows = (len(items) + 2) // 3
        if end_row > total_rows:
            end_row = total_rows
            start_row = max(0, end_row - MAX_ROWS)
            
        start_idx = start_row * 3
        end_idx = end_row * 3
        
        visible_items = items[start_idx:end_idx]
        
        from rich.table import Table
        
        if items[0]["type"] == "action":
            is_active = (active_pane == "right")
            if is_active:
                grid = Text.from_markup("\n\n\n[bold white on red blink]  ☣   INICIAR METAMORFOSIS DEL SISTEMA   ☣  [/]\n\n\n", justify="center")
            else:
                grid = Text.from_markup("\n\n\n[bold green]  🚀   INICIAR METAMORFOSIS DEL SISTEMA   🚀  [/]\n\n\n", justify="center")
        else:
            grid = Table.grid(padding=(2, 2))
            grid.add_column("C1", ratio=1)
            grid.add_column("C2", ratio=1)
            grid.add_column("C3", ratio=1)
            
            cells = []
            if start_row > 0:
                cells.extend(["[dim cyan]... (↑ Arriba)[/dim cyan]", "", ""])
                
            for i_vis, item in enumerate(visible_items):
                actual_i = start_idx + i_vis
                if actual_i >= len(items):
                    break
                    
                is_active = (actual_i == item_idx and active_pane == "right")
                cursor = "[bold yellow]➤[/bold yellow] " if is_active else "  "
                
                chk_box = "[bold green][████] ON [/bold green]" if item.get("selected", False) else "[bold bright_black][░░░░] OFF[/bold bright_black]"
                style = "bold white" if is_active else "dim white"
                if not is_active:
                    chk_box = chk_box.replace("bold", "dim")
                cells.append(f"{cursor}{chk_box} [{style}]{item['label']}[/{style}]")
                    
            while len(cells) % 3 != 0:
                cells.append("")
                
            if end_row < total_rows:
                cells.extend(["[dim cyan]... (↓ Abajo)[/dim cyan]", "", ""])
                
            for i in range(0, len(cells), 3):
                grid.add_row(cells[i], cells[i+1], cells[i+2])

        cat_text = ""
        for i, c in enumerate(menu_data):
            if i == cat_idx:
                style = "bold cyan reverse" if active_pane == "left" else "bold cyan"
                prefix = "▶ " if active_pane == "left" else "  "
                cat_text += f"{prefix}[{style}]{c['cat']}[/{style}]\n\n"
            else:
                style = "dim white" if active_pane == "right" else "white"
                cat_text += f"  [{style}]{c['cat']}[/{style}]\n\n"
        
        # --- NUEVO LAYOUT COMPLETO ESTILO IDE ---
        nav_panel = Panel(
            Align.center(Text.from_markup("[bold cyan]NAVEGACIÓN:[/bold cyan] Flechas [bold yellow]← →[/bold yellow] cambian panel. Flechas [bold yellow]↑ ↓[/bold yellow] mueven selector. [bold yellow]ESPACIO[/bold yellow] alterna.", justify="center"), vertical="middle"),
            title=f"[bold magenta]Configuración Pre-Vuelo[/bold magenta]",
            border_style=border_color
        )
        
        cat_border = "cyan" if active_pane == "left" else "dim white"
        item_border = "green" if active_pane == "right" else "dim white"
        
        cat_panel = Panel(cat_text, title="[bold cyan]Índice de Categorías[/bold cyan]", border_style=cat_border)
        grid_panel = Panel(Align.center(grid, vertical="middle"), title="[bold green]Opciones de Software[/bold green]", border_style=item_border)
        
        current_item = items[item_idx] if active_pane == "right" else menu_data[cat_idx]["items"][0]
        desc = current_item.get("desc", "Sin descripción detallada disponible.")
        
        warning_msg = ""
        if is_legacy_nvidia and "NVIDIA" in current_item["label"].upper():
            warning_msg = "\n\n[bold red]⚠️  ATENCIÓN: Tu hardware ha sido detectado como NVIDIA Legacy. La selección manual de drivers modernos está deshabilitada para prevenir cuelgues del servidor gráfico. El sistema instalará automáticamente el driver legacy correspondiente (390xx o 470xx).[/bold red]"
            
        desc_text = Text.from_markup(f"[bold cyan]Paquete:[/bold cyan] {current_item['label']}\n[bold yellow]Detalles:[/bold yellow] {desc}{warning_msg}\n\n[dim]Usa ESPACIO para alternar el estado del paquete seleccionado.[/dim]", style="white", justify="left")
        desc_panel = Panel(Align.center(desc_text, vertical="middle"), title="[bold yellow]Información Detallada[/bold yellow]", border_style="yellow")
        
        right_layout = Layout()
        right_layout.split_column(
            Layout(grid_panel, ratio=60),
            Layout(desc_panel, ratio=40)
        )
        
        menu_layout = Layout()
        menu_layout.split_row(
            Layout(cat_panel, ratio=35),
            Layout(right_layout, ratio=65)
        )
        
        total_selected = sum(1 for c in menu_data for i in c["items"] if i.get("selected"))
        hud_text = Text.from_markup(f"[bold green]✓ Paquetes marcados para instalación:[/bold green] [bold white]{total_selected}[/bold white]   |   [dim]Presiona ENTER sobre [Iniciar Instalación] para proceder.[/dim]", style="white", justify="center")
        hud_panel = Panel(Align.center(hud_text, vertical="middle"), title="[bold cyan]ESTADO GLOBAL DEL SISTEMA[/bold cyan]", border_style="magenta", height=5, box=box.ROUNDED)
        
        main_layout = Layout()
        main_layout.split_column(
            Layout(nav_panel, size=3),
            Layout(menu_layout, ratio=1),
            Layout(hud_panel, size=5)
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
    global current_state, active_pane, cat_idx, item_idx, user_choices, install_error, install_done, transition_text
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
                        item_idx = max(0, item_idx - 3)
                elif ch == '\x1b[B': # Abajo
                    if active_pane == "left":
                        cat_idx = min(len(menu_data) - 1, cat_idx + 1)
                        item_idx = 0
                    else:
                        item_idx = min(len(menu_data[cat_idx]["items"]) - 1, item_idx + 3)
                elif ch == '\x1b[C': # Derecha
                    if active_pane == "left":
                        active_pane = "right"
                    else:
                        item_idx = min(len(menu_data[cat_idx]["items"]) - 1, item_idx + 1)
                elif ch == '\x1b[D': # Izquierda
                    if active_pane == "right":
                        if item_idx % 3 == 0:
                            active_pane = "left"
                        else:
                            item_idx = max(0, item_idx - 1)
                elif ch == ' ':
                    if active_pane == "right":
                        item = menu_data[cat_idx]["items"][item_idx]
                        if item["type"] == "toggle":
                            if is_legacy_nvidia and "NVIDIA" in item["label"]:
                                sys.stdout.write('\a')
                                sys.stdout.flush()
                            else:
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
                            if is_legacy_nvidia and "NVIDIA" in item["label"]:
                                sys.stdout.write('\a')
                                sys.stdout.flush()
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

def setup_plymouth_bootloader(has_nvidia_gpu=False):
    log_lines.append("[yellow]Instalando plymouth...[/yellow]")
    run_cmd_live("sudo pacman -S --noconfirm --needed plymouth", check=False)
    
    log_lines.append("[yellow]Aplicando tema de Plymouth...[/yellow]")
    run_cmd_live("sudo mkdir -p /usr/share/plymouth/themes/omarchy", check=False)
    run_cmd_live("sudo cp -r default/plymouth/* /usr/share/plymouth/themes/omarchy/ 2>/dev/null", check=False)
    run_cmd_live("sudo plymouth-set-default-theme omarchy", check=False)
    
    log_lines.append("[yellow]Configurando mkinitcpio (HOOKS & KMS)...[/yellow]")
    # Soporte para mkinitcpio clásico (udev) y moderno (systemd)
    run_cmd_live("sudo bash -c 'grep -q \" plymouth\" /etc/mkinitcpio.conf || sed -i -E \"s/^(HOOKS=\\([^)]*\\b)(udev|systemd)(\\b)/\\1\\2 plymouth/\" /etc/mkinitcpio.conf' 2>/dev/null", check=False)
    
    if has_nvidia_gpu:
        log_lines.append("[yellow]Inyectando Early KMS para NVIDIA...[/yellow]")
        run_cmd_live("sudo bash -c 'sed -i -E \"s/^MODULES=\\(([^)]*)\\)/MODULES=(\\1 nvidia nvidia_modeset nvidia_uvm nvidia_drm)/\" /etc/mkinitcpio.conf' 2>/dev/null", check=False)
        run_cmd_live("sudo bash -c 'sed -i \"s/nvidia nvidia/nvidia/g\" /etc/mkinitcpio.conf' 2>/dev/null", check=False) # Cleanup duplicates
    
    # Aceleración multicore para mkinitcpio (Purgar configuración anterior y forzar array de bash)
    run_cmd_live("sudo sed -i '/COMPRESSION/d' /etc/mkinitcpio.conf", check=False)
    run_cmd_live("sudo bash -c 'cat <<EOF >> /etc/mkinitcpio.conf\nCOMPRESSION=\"zstd\"\nCOMPRESSION_OPTIONS=(\"-T0\")\nEOF'", check=False)
    # Regenerar initramfs explícitamente y silenciar advertencias de limine
    run_cmd_live("echo '' | sudo mkinitcpio -P", check=False)
    
    log_lines.append("[yellow]Configurando Dracut (Fallback)...[/yellow]")
    run_cmd_live("sudo mkdir -p /etc/dracut.conf.d", check=False)
    run_cmd_live("sudo bash -c 'echo \"add_dracutmodules+=\\\" plymouth \\\"\" > /etc/dracut.conf.d/plymouth.conf'", check=False)
    if has_nvidia_gpu:
        run_cmd_live("sudo bash -c 'echo \"force_drivers+=\\\" nvidia nvidia_modeset nvidia_uvm nvidia_drm \\\"\" >> /etc/dracut.conf.d/plymouth.conf'", check=False)
    
    log_lines.append("[yellow]Buscando e inyectando configuración en Limine...[/yellow]")
    # Inyectar en cmdline base (usado por cachyos/limine-entry-tool)
    cmdline_extra = " splash"
    if has_nvidia_gpu:
        cmdline_extra += " nvidia_drm.modeset=1 nvidia_drm.fbdev=1"
        
    run_cmd_live(f"sudo bash -c 'if [ -f /etc/kernel/cmdline ]; then grep -q \"splash\" /etc/kernel/cmdline || sed -i \"s/$/{cmdline_extra}/\" /etc/kernel/cmdline; fi' 2>/dev/null", check=False)
    
    # Inyectar directamente en limine.conf por si no usan limine-entry-tool
    run_cmd_live(f"sudo find /boot /efi -maxdepth 4 \\( -name 'limine.conf' -o -name 'limine.cfg' \\) -exec bash -c 'grep -q \"splash\" \"$1\" || sudo sed -i -E \"/^ *kernel_cmdline/ {{ /splash/! s/$/{cmdline_extra}/ }}\" \"$1\"' _ {{}} \\; 2>/dev/null", check=False)
    run_cmd_live(f"sudo find /boot /efi -maxdepth 4 \\( -name 'limine.conf' -o -name 'limine.cfg' \\) -exec bash -c 'grep -q \"splash\" \"$1\" || sudo sed -i -E \"/^ *cmdline/ {{ /splash/! s/$/{cmdline_extra}/ }}\" \"$1\"' _ {{}} \\; 2>/dev/null", check=False)
    
    # Actualizar limine si está instalado (ignorando prompts)
    run_cmd_live("if command -v limine-update >/dev/null; then echo '' | sudo limine-update; fi", check=False)

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
        progress.update(t_repo, description="[yellow]Inyectando Chaotic-AUR...", advance=10)
        run_cmd_live("sudo pacman-key --recv-key 3056513887B78AEB --keyserver keyserver.ubuntu.com", check=False)
        run_cmd_live("sudo pacman-key --lsign-key 3056513887B78AEB", check=False)
        run_cmd_live("sudo pacman -U --noconfirm 'https://cdn-mirror.chaotic.cx/chaotic-aur/chaotic-keyring.pkg.tar.zst' 'https://cdn-mirror.chaotic.cx/chaotic-aur/chaotic-mirrorlist.pkg.tar.zst'", check=False)
        run_cmd_live("sudo bash -c 'grep -q \"chaotic-aur\" /etc/pacman.conf || echo -e \"\\n[chaotic-aur]\\nInclude = /etc/pacman.d/chaotic-mirrorlist\\n\" >> /etc/pacman.conf'")
        progress.update(t_repo, description="[green]Repositorios Listos", completed=100)


        progress.update(t_sync, description="[yellow]Creando Snapshot BTRFS...", advance=5)
        run_cmd_live("sudo snapper create -c root -d 'Pre-Omarchy Installation'", check=False)
        progress.update(t_sync, description="[yellow]Sincronizando firmas (Puede tardar)...", advance=10)
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
        
        # Copiado acelerado mediante Python nativo (shutil)
        shutil.copytree("config", os.path.expanduser("~/.config"), dirs_exist_ok=True)
        
        if is_legacy_nvidia:
            autostart_path = os.path.expanduser("~/.config/hypr/autostart.lua")
            if os.path.exists(autostart_path):
                with open(autostart_path, "a") as f:
                    f.write('\no.launch_on_start("killall waybar swaybg")\n')
                    f.write('o.launch_on_start("quickshell -n -p /usr/share/omarchy/shell")\n')
                    
        shutil.copytree("bin", os.path.expanduser("~/.local/bin"), dirs_exist_ok=True)
        shutil.copytree("themes", os.path.expanduser("~/.local/share/themes"), dirs_exist_ok=True)
        run_cmd_live("chmod +x ~/.local/bin/*", check=False)
        
        progress.update(t_config, description="[yellow]Configurando Pantalla de Arranque (Plymouth)...", advance=5)
        setup_plymouth_bootloader(has_nvidia)
        
        progress.update(t_config, description="[yellow]Desplegando Gestor TUI (Tuigreet)...", advance=5)
        
        # --- Instalar Greetd + Tuigreet ---
        run_cmd_live("sudo pacman -S --noconfirm greetd greetd-tuigreet", check=False)
        run_cmd_live("sudo mkdir -p /etc/greetd", check=False)
        
        # Parche de seguridad para evitar que Plymouth congele la TTY1 tapando a Tuigreet
        run_cmd_live("sudo mkdir -p /etc/systemd/system/greetd.service.d", check=False)
        run_cmd_live("sudo bash -c 'cat << \"EOF\" > /etc/systemd/system/greetd.service.d/plymouth-fix.conf\n[Service]\nExecStartPre=-/usr/bin/plymouth quit\nEOF'", check=False)
        
        # --- Configurar Sesiones ---
        if is_legacy_nvidia:
            # Crear sesión Legacy
            legacy_session = """[Desktop Entry]
Name=Omarchy (Legacy)
Exec=Hyprland
Type=Application
"""
            run_cmd_live("sudo mkdir -p /usr/share/wayland-sessions", check=False)
            run_cmd_live(f"sudo bash -c 'cat << \"EOF\" > /usr/share/wayland-sessions/omarchy-legacy.desktop\n{legacy_session}EOF'", check=False)
            
            greetd_config = """[terminal]
vt = 1
[default_session]
command = "tuigreet --cmd 'Hyprland' --asterisks --time --greeting 'NVIDIA Legacy Fallback Protocol' --remember --remember-user-session --sessions /usr/share/wayland-sessions"
user = "greeter"
"""
        else:
            greetd_config = """[terminal]
vt = 1
[default_session]
command = "tuigreet --cmd 'uwsm start hyprland-uwsm.desktop' --asterisks --time --greeting 'Bienvenido a Omarchy Cyberpunk Environment' --remember --remember-user-session --sessions /usr/share/wayland-sessions"
user = "greeter"
"""

        run_cmd_live(f"sudo bash -c 'cat << \"EOF\" > /etc/greetd/config.toml\n{greetd_config}EOF'", check=False)

        if not is_legacy_nvidia:
            progress.update(t_config, description="[yellow]Configurando Tema SDDM...", advance=5)
            run_cmd_live("sudo mkdir -p /usr/share/sddm/themes/omarchy", check=False)
            run_cmd_live("sudo cp -r default/sddm/omarchy/* /usr/share/sddm/themes/omarchy/ 2>/dev/null", check=False)
            run_cmd_live("sudo mkdir -p /etc/sddm.conf.d", check=False)
            run_cmd_live("sudo bash -c 'echo -e \"[Theme]\\nCurrent=omarchy\" > /etc/sddm.conf.d/omarchy.conf'", check=False)
            
            progress.update(t_config, description="[yellow]Habilitando servicios...", advance=10)
            run_cmd_live("sudo systemctl disable greetd.service 2>/dev/null", check=False)
            run_cmd_live("sudo systemctl enable sddm.service --now", check=False)
        else:
            progress.update(t_config, description="[yellow]Habilitando Tuigreet (Legacy Hardware)...", advance=15)
            run_cmd_live("sudo systemctl disable sddm.service 2>/dev/null", check=False)
            run_cmd_live("sudo systemctl enable greetd.service --now", check=False)


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
            run_cmd_live("export OMARCHY_PATH=/usr/share/omarchy && export OMARCHY_THEME_HEADLESS=1 && /usr/share/omarchy/bin/omarchy-theme-set 'Tokyo Night'", check=False)
        
        progress.update(t_config, description="[green]Sistema Listo", completed=100)
        
        if is_legacy_nvidia:
            run_cmd_live("echo -e '\n\033[1;41m[ ALERTA NVIDIA LEGACY ]\033[0m\nHardware antiguo detectado. El protocolo de rescate se ha inyectado. Por favor, inicia sesión escribiendo: \033[1;33mHyprland\033[0m (No uses UWSM ni el display manager).'", check=False)
            time.sleep(5)
            
    except Exception as e:
        install_error = str(e)
    finally:
        install_done = True
        current_state = "error" if install_error else "done"

# --- Hardware Auto-Detect ---
def detect_gpu_and_update_menu():
    global is_legacy_nvidia
    try:
        import subprocess
        chk = subprocess.run(["lspci"], stdout=subprocess.PIPE, text=True, check=False)
        output = chk.stdout.lower()
        has_nvidia = False
        for line in output.split('\n'):
            if ('vga' in line or '3d' in line) and 'nvidia' in line:
                has_nvidia = True
                break
        
        if has_nvidia:
            try:
                pacman_q = subprocess.run(["pacman", "-Q"], stdout=subprocess.PIPE, text=True, check=False)
                installed_pkgs = pacman_q.stdout.lower()
                if "nvidia-580xx-dkms" in installed_pkgs or "nvidia-470xx-dkms" in installed_pkgs or "nvidia-390xx-dkms" in installed_pkgs:
                    is_legacy_nvidia = True
            except Exception:
                pass
        
        for cat in menu_data:
            if "13. Drivers Gráficos" in cat["cat"]:
                for item in cat["items"]:
                    if "NVIDIA" in item["label"]:
                        item["selected"] = has_nvidia and not is_legacy_nvidia
                        if is_legacy_nvidia:
                            item["desc"] += " [bold red](Bloqueado: Hardware Legacy Detectado)[/bold red]"
                    elif "Mesa" in item["label"]:
                        item["selected"] = not has_nvidia
    except Exception:
        pass

# --- Launch Sequence ---
with open(LOG_FILE, "w") as f:
    f.write("=== Inicio de Instalación X64-Omarchy (Mega Dashboard) ===\n")

detect_gpu_and_update_menu()

k_worker = threading.Thread(target=keyboard_worker, daemon=True)
k_worker.start()

try:
    with Live(update_ui(), refresh_per_second=30, screen=True) as live:
        while not install_done:
            time.sleep(0.02)
            
            if current_state == "error" and error_prompt:
                live.stop()
                os.system("clear")
                print(f"\n\033[1;41m[ ATENCIÓN - ERROR CRÍTICO ]\033[0m")
                print(f"\033[1;33m{error_prompt['msg']}\033[0m\n")
                ans = Prompt.ask("¿Cómo deseas proceder?", choices=["Reintentar", "Ignorar", "Abortar"], default="Reintentar")
                error_response = ans
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
    
    ans = Prompt.ask("\n¿Deseas reiniciar el sistema ahora?", choices=["Si", "No"], default="Si")
    if ans == "Si":
        os.system("sudo reboot")
    else:
        print("\n[!] Puedes reiniciar más tarde ejecutando 'reboot'.\n")
else:
    console.print(Panel(f"[bold red]La instalación fue abortada: {install_error}[/bold red]", expand=False))

try:
    os.system(f"sudo cp {LOG_FILE} /var/log/x64-omarchy-install.log 2>/dev/null")
except Exception:
    pass
