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
import asyncio
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
error_idx = 0

plymouth_modal_idx = 0
install_plymouth_flag = False
install_plymouth_theme_name = "omarchy"

# --- Unified Menu State ---
with open("core/menu_data.json", "r", encoding="utf-8") as f:
    menu_data = json.load(f)

active_pane = "left"
cat_idx = 0
item_idx = 0
user_choices = {"theme": "Tokyo Night", "packages": []}
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

def log(msg):
    time_str = datetime.now().strftime('%H:%M:%S')
    with open(LOG_FILE, "a") as f:
        f.write(f"[{time_str}] {msg}\n")
    log_lines.append(f"[bold blue][{time_str}][/bold blue] [bold cyan]{msg}[/bold cyan]")

def run_cmd_live(cmd, check=True):
    global error_prompt, error_response, current_state
    
    async def _run():
        global error_prompt, error_response, current_state
        while True:
            log(f"Ejecutando (async): {cmd}")
            process = await asyncio.create_subprocess_shell(
                cmd,
                stdin=asyncio.subprocess.DEVNULL,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT
            )
            
            last_lines = []
            with open(LOG_FILE, "a", buffering=8192) as f:
                async for line_bytes in process.stdout:
                    line_clean = line_bytes.decode('utf-8', errors='replace').strip()
                    if line_clean:
                        f.write(line_clean + "\n")
                        last_lines.append(line_clean)
                        if len(last_lines) > 5:
                            last_lines.pop(0)
                        # Mitigación I/O: Reducir drásticamente la basura visual. Solo alertar de errores críticos.
                        lower_line = line_clean.lower()
                        if "fatal" in lower_line or "error" in lower_line or "failed" in lower_line or "warning" in lower_line:
                            safe_line = escape(line_clean)
                            log_lines.append(f"[dim red]{safe_line}[/dim red]")
                        
            await process.wait()
            
            if check and process.returncode != 0:
                log(f"FALLO: El comando devolvió código {process.returncode}")
                current_state = "error"
                err_details = "\n".join(last_lines)
                error_prompt = {"msg": f"El comando falló con código {process.returncode}:\n{cmd}\n\n[bold white]Detalles del Error (Últimas líneas):[/bold white]\n[red]{escape(err_details)}[/red]"}
                
                # Flush the input buffer so that if the user pressed Enter/Arrows while it was frozen, it doesn't auto-abort
                try:
                    import termios
                    termios.tcflush(sys.stdin.fileno(), termios.TCIFLUSH)
                except Exception:
                    pass
                
                while error_response is None:
                    await asyncio.sleep(0.1)
                    
                resp = error_response
                error_response = None
                error_prompt = None
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
            
    return asyncio.run(_run())

# --- System Info (Panel Izquierdo: Fastfetch + Live) ---
def get_sys_info():
    table = Table(show_header=False, expand=True, box=None)
    
    if not hasattr(get_sys_info, "ff_text"):
        get_sys_info.ff_text = ""
        get_sys_info.last_update = 0
        get_sys_info.cached_rows = []
        try:
            res = subprocess.run(["fastfetch", "--logo", "none", "--structure", "OS:Host:Kernel:Display:CPU:GPU:Memory:Disk:Battery:Vulkan:OpenGL"], stdout=subprocess.PIPE, text=True)
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
t_final = progress.add_task("[white]Finalizando Instalación...", total=100)

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
    from rich.console import Console
    console = Console()
    
    # LAYOUT DINÁMICO: Ocultar logo si la terminal es pequeña para evitar desbordamiento
    if console.size.height < 30:
        layout["left"]["logo"].visible = False
    else:
        layout["left"]["logo"].visible = True
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
                
                if "Entornos" in menu_data[cat_idx]["cat"]:
                    chk_box = "[bold green]( ◉ ) ON  [/bold green]" if item.get("selected", False) else "[bold bright_black]( ◯ ) OFF [/bold bright_black]"
                else:
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
        cat_border = "cyan" if active_pane == "left" else "dim white"
        item_border = "green" if active_pane == "right" else "dim white"
        
        cat_panel = Panel(cat_text, title="[bold cyan]Índice de Categorías[/bold cyan]", border_style=cat_border)
        grid_panel = Panel(Align.center(grid, vertical="middle"), title="[bold green]Opciones de Software[/bold green]", border_style=item_border)
        
        current_item = items[item_idx] if active_pane == "right" else menu_data[cat_idx]["items"][0]
        desc = current_item.get("desc", "Sin descripción detallada disponible.")
        
        warning_msg = ""
        if is_legacy_nvidia and "NVIDIA" in current_item["label"].upper():
            warning_msg = "\n\n[bold red]⚠️  ATENCIÓN: Tu hardware ha sido detectado como NVIDIA de arquitectura antigua. El sistema instalará los drivers modernos DKMS, pero habilitará el protocolo de rescate TTY Pura para evitar colapsos del servidor gráfico.[/bold red]"
            
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
        hud_text = Text.from_markup(f"[bold cyan]Navegación:[/bold cyan] Flechas [bold yellow]←↑↓→[/bold yellow] | [bold yellow]ESPACIO[/bold yellow] Alternar | [bold green]✓ Seleccionados:[/bold green] [bold white]{total_selected}[/bold white] | [dim]ENTER sobre [Iniciar] para instalar[/dim]", style="white", justify="center")
        hud_panel = Panel(Align.center(hud_text, vertical="middle"), title="[bold cyan]ESTADO GLOBAL DEL SISTEMA[/bold cyan]", border_style="magenta", height=3, box=box.ROUNDED)
        
        main_layout = Layout()
        main_layout.split_column(
            Layout(menu_layout, ratio=1),
            Layout(hud_panel, size=3)
        )
        layout["right"].update(main_layout)

    elif current_state == "plymouth_modal":
        theme_name = "Omarchy Oficial"
        for c in menu_data:
            if "Entornos" in c["cat"]:
                for i in c["items"]:
                    if i.get("selected") and "X64 Studios" in i["label"]:
                        theme_name = "X64 Studios"
                        break
        
        modal_text = Text.from_markup(f"\n[bold yellow]¿Deseas instalar la Pantalla de Carga Animada (Plymouth)?[/bold yellow]\n\nEsta opción inyectará el logotipo animado de [bold cyan]{theme_name}[/bold cyan] al encender tu PC, dándote un inicio premium.\nSin embargo, este proceso requiere reconstruir el núcleo del sistema, lo que [bold red]añadirá varios minutos extra[/bold red] al tiempo de instalación.\n\n", justify="center")
        
        if plymouth_modal_idx == 0:
            btn_text = Text.from_markup("[bold reverse green] > SÍ, INSTALAR < [/bold reverse green]      [bold white]   NO, OMITIR   [/bold white]", justify="center")
        else:
            btn_text = Text.from_markup("[bold white]   SÍ, INSTALAR   [/bold white]      [bold reverse red] > NO, OMITIR < [/bold reverse red]", justify="center")
            
        from rich.console import Group
        modal_content = Group(modal_text, btn_text)
        layout["right"].update(Panel(Align.center(modal_content, vertical="middle"), title="[bold white]Ajuste de Inicio del Sistema[/bold white]", border_style="yellow"))

    elif current_state == "error" and error_prompt:
        ui_transitioned = False
        layout["right"].unsplit()
        
        error_text = Text.from_markup(f"\n[bold red blink]⚠️  ERROR CRÍTICO DETECTADO  ⚠️[/bold red blink]\n\n[bold yellow]{error_prompt['msg']}[/bold yellow]\n\n[cyan]Elige cómo proceder (Usa las flechas ← y →, presiona ENTER para confirmar):[/cyan]\n", justify="center")
        
        opt1 = "[bold black on white] > REINTENTAR < [/]" if error_idx == 0 else "  Reintentar  "
        opt2 = "[bold black on white] > IGNORAR < [/]" if error_idx == 1 else "  Ignorar  "
        opt3 = "[bold black on white] > ABORTAR < [/]" if error_idx == 2 else "  Abortar  "
        
        opts = Text.from_markup(f"\n{opt1}    {opt2}    {opt3}\n", justify="center")
        
        from rich.console import Group
        panel = Panel(Align.center(Group(error_text, opts), vertical="middle"), border_style="red", title="[bold red]ATENCIÓN[/bold red]")
        layout["right"].update(panel)
        
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
        matrix_text = "\n".join(list(log_lines)[-12:])
        matrix_obj = Text.from_markup(matrix_text, overflow="crop")
        matrix_obj.no_wrap = True
        layout["right"]["matrix"].update(Panel(matrix_obj, title="[bold yellow]The Matrix (Live Log)[/bold yellow]", border_style="yellow"))
        
    return layout



def setup_plymouth_bootloader(has_nvidia_gpu=False, theme_name="omarchy"):
    log_lines.append(f"[yellow]Aplicando tema de Plymouth ({theme_name})...[/yellow]")
    if theme_name == "x64-studios":
        run_cmd_live("sudo mkdir -p /usr/share/plymouth/themes/x64-studios", check=False)
        run_cmd_live("sudo cp -r default/plymouth-x64/* /usr/share/plymouth/themes/x64-studios/ 2>/dev/null", check=False)
        run_cmd_live("sudo plymouth-set-default-theme x64-studios", check=False)
    else:
        run_cmd_live("sudo mkdir -p /usr/share/plymouth/themes/omarchy", check=False)
        run_cmd_live("sudo cp -r default/plymouth/* /usr/share/plymouth/themes/omarchy/ 2>/dev/null", check=False)
        run_cmd_live("sudo plymouth-set-default-theme omarchy", check=False)
    
    log_lines.append("[yellow]Configurando mkinitcpio (HOOKS & KMS)...[/yellow]")
    # Soporte para mkinitcpio clásico (udev) y moderno (systemd)
    run_cmd_live("sudo bash -c 'grep -q \" plymouth\" /etc/mkinitcpio.conf || sed -i -E \"s/^(HOOKS=\\([^)]*\\b)(udev|systemd)(\\b)/\\1\\2 plymouth/\" /etc/mkinitcpio.conf' 2>/dev/null", check=False)
    
    if has_nvidia_gpu:
        log_lines.append("[yellow]Inyectando Early KMS para NVIDIA...[/yellow]")
        run_cmd_live("sudo bash -c 'grep -q \"nvidia_drm?\" /etc/mkinitcpio.conf || sed -i -E \"s/^MODULES=\\(([^)]*)\\)/MODULES=(\\1 nvidia? nvidia_modeset? nvidia_uvm? nvidia_drm?)/\" /etc/mkinitcpio.conf' 2>/dev/null", check=False)
        run_cmd_live("sudo bash -c 'sed -i \"s/nvidia nvidia/nvidia/g\" /etc/mkinitcpio.conf' 2>/dev/null", check=False) # Cleanup duplicates
    
    # Aceleración multicore para mkinitcpio (Purgar configuración anterior y forzar array de bash)
    run_cmd_live("sudo sed -i '/COMPRESSION/d' /etc/mkinitcpio.conf", check=False)
    with open("/tmp/mkinitcpio_add.conf", "w") as f:
        f.write('COMPRESSION="zstd"\nCOMPRESSION_OPTIONS=("-T0")\n')
    run_cmd_live("sudo bash -c 'cat /tmp/mkinitcpio_add.conf >> /etc/mkinitcpio.conf'", check=False)
    
    # Asegurar que todos los módulos DKMS (como nvidia-470xx-dkms legacy) estén compilados para el kernel actual
    log_lines.append("[yellow]Compilando módulos DKMS (Multihilo)...[/yellow]")
    run_cmd_live("sudo dkms autoinstall -j $(nproc)", check=False)
    
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
        run_cmd_live("sudo mkdir -p /etc/modprobe.d", check=False)
        run_cmd_live("sudo bash -c 'echo \"options nvidia_drm modeset=1 fbdev=1\" > /etc/modprobe.d/nvidia-kms.conf'", check=False)
        
    run_cmd_live(f"sudo bash -c 'if [ -f /etc/kernel/cmdline ]; then grep -q \"splash\" /etc/kernel/cmdline || sed -i \"s/$/{cmdline_extra}/\" /etc/kernel/cmdline; fi' 2>/dev/null", check=False)
    
    # Búsqueda optimizada de Limine nativa (Sin escaneos ciegos)
    limine_paths = ["/boot/limine.conf", "/boot/limine/limine.conf", "/efi/limine.conf", "/boot/efi/limine.conf",
                    "/boot/limine.cfg", "/boot/limine/limine.cfg", "/efi/limine.cfg", "/boot/efi/limine.cfg"]
    for lpath in limine_paths:
        if os.path.exists(lpath):
            run_cmd_live(f"sudo bash -c 'grep -q \"splash\" {lpath} || sudo sed -i -E \"/^ *kernel_cmdline/ {{ /splash/! s/$/{cmdline_extra}/ }}\" {lpath}' 2>/dev/null", check=False)
            run_cmd_live(f"sudo bash -c 'grep -q \"splash\" {lpath} || sudo sed -i -E \"/^ *cmdline/ {{ /splash/! s/$/{cmdline_extra}/ }}\" {lpath}' 2>/dev/null", check=False)
            break
    
    # Actualizar limine si está instalado (ignorando prompts)
    run_cmd_live("if command -v limine-update >/dev/null; then echo '' | sudo limine-update; fi", check=False)

def installer_worker():
    global install_error, install_done, current_state
    try:
        install_hyprland = "hyprland" in user_choices["packages"]
        if not install_hyprland:
            user_choices["theme"] = "CachyOS Nativo"
        is_wayland_env = any(pkg in user_choices["packages"] for pkg in ["hyprland", "plasma-meta", "niri"])
        force_tty = is_legacy_nvidia and is_wayland_env
        progress.update(t_health, description="[yellow]Verificando Red...", advance=30)
        run_cmd_live("curl -s -I https://archlinux.org >/dev/null")
        progress.update(t_health, description="[yellow]Verificando Espacio en Disco...", advance=30)
        free_space = shutil.disk_usage("/").free
        if free_space < 15 * 1024 * 1024 * 1024:
            raise Exception("Espacio insuficiente. Se requieren al menos 15GB libres en /.")

        progress.update(t_health, description="[green]Sistema en Óptimas Condiciones", completed=100)
        
        progress.update(t_repo, description="[yellow]Acelerando Descargas (ParallelDownloads)...", advance=10)
        run_cmd_live("sudo sed -i 's/^#ParallelDownloads.*/ParallelDownloads = 10/' /etc/pacman.conf", check=False)
        run_cmd_live("sudo bash -c 'grep -q \"^ILoveCandy\" /etc/pacman.conf || sed -i \"/^#Color/a ILoveCandy\" /etc/pacman.conf'", check=False)
        run_cmd_live("sudo sed -i '/NoExtract = usr\\/share\\/doc\\/\\*/d' /etc/pacman.conf", check=False)
        run_cmd_live("sudo bash -c 'grep -q \"NoExtract = usr/share/doc\" /etc/pacman.conf || sed -i \"/^\\[options\\]/a NoExtract = usr/share/doc/* usr/share/gtk-doc/* usr/share/help/* usr/share/man/* usr/share/info/*\" /etc/pacman.conf'", check=False)
        
        progress.update(t_repo, description="[yellow]Desbloqueando Pacman...", advance=10)
        if os.path.exists("/var/lib/pacman/db.lck"):
            run_cmd_live("sudo rm -f /var/lib/pacman/db.lck")
        
        progress.update(t_repo, description="[yellow]Inyectando Chaotic-AUR...", advance=50)
        run_cmd_live("sudo sed -i '/\\[chaotic-aur\\]/,+2d' /etc/pacman.conf", check=False)
        run_cmd_live("sudo pacman-key --recv-key 3056513887B78AEB --keyserver keyserver.ubuntu.com", check=False)
        run_cmd_live("sudo pacman-key --lsign-key 3056513887B78AEB", check=False)
        run_cmd_live("sudo pacman -U --noconfirm 'https://cdn-mirror.chaotic.cx/chaotic-aur/chaotic-keyring.pkg.tar.zst' 'https://cdn-mirror.chaotic.cx/chaotic-aur/chaotic-mirrorlist.pkg.tar.zst'", check=False)
        run_cmd_live("sudo bash -c 'if [ -f /etc/pacman.d/chaotic-mirrorlist ]; then grep -q \"chaotic-aur\" /etc/pacman.conf || echo -e \"\\n[chaotic-aur]\\nInclude = /etc/pacman.d/chaotic-mirrorlist\\n\" >> /etc/pacman.conf; fi'")
        
        if install_hyprland:
            progress.update(t_repo, description="[yellow]Purgando dependencias en conflicto pre-existentes...", advance=10)
            run_cmd_live("sudo pacman -Rdd --noconfirm quickshell noctalia-qs 2>/dev/null", check=False)
            progress.update(t_repo, description="[yellow]Inyectando repo Omarchy...", advance=10)
            # Ensure omarchy repo is injected with high priority (before cachyos and core)
            inject_script = """
import re
import sys
conf = open('/etc/pacman.conf').read()

# Auto-sanar URL rota de versiones previas
if 'https://pkgs.omarchy.org//' in conf:
    conf = conf.replace('https://pkgs.omarchy.org//', 'https://pkgs.omarchy.org/\\$arch/')
    open('/etc/pacman.conf', 'w').write(conf)

if '[omarchy]' not in conf:
    match = re.search(r'^\\[(?!options\\]).*?\\]', conf, re.MULTILINE)
    if match:
        idx = match.start()
        new_conf = conf[:idx] + '[omarchy]\\nSigLevel = Optional TrustAll\\nServer = https://pkgs.omarchy.org/\\$arch/\\n\\n' + conf[idx:]
        open('/etc/pacman.conf', 'w').write(new_conf)
"""
            run_cmd_live(f"sudo python -c \"{inject_script}\"")
        
        progress.update(t_repo, description="[green]Repositorios Listos", completed=100)

        progress.update(t_sync, description="[yellow]Creando Snapshot BTRFS...", advance=5)
        run_cmd_live("sudo snapper create -c root -d 'Pre-Omarchy Installation'", check=False)
        
        progress.update(t_sync, description="[yellow]Instalando Cabeceras del Kernel (Para DKMS)...", advance=5)
        run_cmd_live("sudo bash -c 'pacman -S --noconfirm --needed $(pacman -Qq | grep \"^linux\" | grep -v \"headers\" | grep -v \"firmware\" | awk \"{print \\$1\\\"-headers\\\"}\")' 2>/dev/null", check=False)


        progress.update(t_sync, description="[yellow]Sincronizando firmas (Puede tardar)...", advance=3)
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
        if install_hyprland:
            if os.path.exists("install/omarchy-base.packages"):
                with open("install/omarchy-base.packages") as f1:
                    pkgs.extend(f1.read().splitlines())
            if os.path.exists("install/omarchy-other.packages"):
                with open("install/omarchy-other.packages") as f2:
                    pkgs.extend(f2.read().splitlines())
        
        # Filtro Negro (Blacklist) de X64 para proteger CachyOS de upstream
        blacklisted_pkgs = {
            "linux-ptl", "linux-t2", "linux", "linux-firmware", "linux-headers", "linux-ptl-headers",
            "linux-firmware-marvell", "linux-t2-headers", "limine", "limine-mkinitcpio-hook", "limine-snapper-sync",
            "nvidia-580xx-dkms", "nvidia-dkms", "nvidia-open-dkms", "nvidia-580xx-utils", "nvidia-utils",
            "lib32-nvidia-580xx-utils", "lib32-nvidia-utils", "libva-nvidia-driver", "intel-media-driver",
            "intel-lpmd", "intel-ipu7-camera", "broadcom-wl-dkms", "macbook12-spi-driver-dkms",
            "tuxedo-drivers-nocompatcheck-dkms", "yt6801-dkms", "apple-bcm-firmware", "apple-t2-audio-config",
            "t2fanrd", "qmk-hid", "dell-xps-touchpad-haptics", "dell-xps13-sidecar-amps",
            "vulkan-intel", "vulkan-radeon", "vulkan-asahi", "yay-debug", "btrfs-progs", "sof-firmware",
            "base", "base-devel", "dkms", "asusctl", "quickshell"
        }
        pkgs = [p for p in pkgs if p and not p.startswith('#') and p not in blacklisted_pkgs]

        # Batch de paquetes críticos de sistema
        pkgs.extend(["xorg-xinit", "xorg-server", "nwg-displays", "waypaper", "firefox", "python-pyqt6", "qt6-declarative", "qt6-5compat", "qt6-svg"])
        pkgs.extend(user_choices["packages"])
        pkgs = list(set(pkgs))
        pkg_str = " ".join([p for p in pkgs if p and not p.startswith('#')])
        
        env_pkgs_to_remove = []
        for c in menu_data:
            if "Entornos" in c["cat"]:
                for i in c["items"]:
                    if not i.get("selected"):
                        env_pkgs_to_remove.extend(i.get("pkg", []))
        
        # Protegemos los paquetes que SÍ fueron seleccionados (ej: 'kitty' es compartido entre Niri y Cinnamon)
        env_pkgs_to_remove = set(env_pkgs_to_remove) - set(user_choices["packages"])
        
        # Quitamos de la lista a instalar los paquetes de los entornos NO seleccionados
        # (Esto previene que se instalen aunque vengan hardcodeados en el omarchy-base.packages original)
        pkgs = list(set(pkgs) - env_pkgs_to_remove)
        pkg_str = " ".join([p for p in pkgs if p and not p.startswith('#')])

        to_remove = set(env_pkgs_to_remove)
        if to_remove:
            remove_str = " ".join([p for p in to_remove if p and not p.startswith('#')])
            progress.update(t_pkg, description="[yellow]Purgando entornos anteriores...", advance=5)
            run_cmd_live(f"sudo bash -c 'installed=$(pacman -Qq {remove_str} 2>/dev/null); if [ -n \"$installed\" ]; then for pkg in $installed; do pacman -Rns --noconfirm $pkg 2>/dev/null || pacman -R --noconfirm $pkg 2>/dev/null; done; fi'", check=False)
        
        chk = subprocess.run(f"pacman -T {pkg_str}", shell=True, stdout=subprocess.PIPE, text=True)
        if chk.returncode != 0:
            missing_pkgs = [p for p in chk.stdout.splitlines()]
            progress.update(t_pkg, description="[cyan]Descargando e Instalando Paquetes (Puede tardar varios minutos)...", advance=40)
            run_cmd_live("sudo pacman -Rdd --noconfirm jack2 2>/dev/null", check=False)
            run_cmd_live("sudo pacman -Rdd --noconfirm noctalia-shell noctalia-qs quickshell 2>/dev/null", check=False)

            run_cmd_live(f"sudo pacman -S --noconfirm --needed {' '.join(missing_pkgs)}")
        progress.update(t_pkg, description="[green]Paquetes Instalados", completed=100)

        progress.update(t_backup, description="[yellow]Comprimiendo ~/.config...", advance=50)
        home = os.path.expanduser("~")
        backup_name = f"x64-backup-{datetime.now().strftime('%Y%m%d_%H%M%S')}.tar.gz"
        run_cmd_live(f"tar -czf {backup_name} -C {home} .config 2>/dev/null", check=False)
        progress.update(t_backup, description="[green]Respaldo Completado", completed=100)

        progress.update(t_config, description="[yellow]Desplegando escudo de sistema...", advance=20)
        
        if install_hyprland:
            run_cmd_live("mkdir -p ~/.config ~/.local/bin ~/.local/share/themes")
            run_cmd_live("sudo rm -rf /usr/share/omarchy")
            run_cmd_live("sudo git clone -b quattro https://github.com/XzForz3-Dev/X64-Omarchy-CachyOS.git /usr/share/omarchy")
            run_cmd_live("sudo git config --system --add safe.directory /usr/share/omarchy")
            
            # FIX(updater): Ensure the user owns the directory so the GUI can run git pull without sudo
            run_cmd_live("sudo chown -R $USER:$USER /usr/share/omarchy")
            
            # Dinamicamente inyectar scale = "auto" para pantallas HiDPI
            run_cmd_live("sudo sed -i 's/scale = 1/scale = \"auto\"/g' /usr/share/omarchy/config/hypr/monitors.lua")

            run_cmd_live("sudo mkdir -p /usr/share/wayland-sessions")
            run_cmd_live("sudo cp default/wayland-sessions/*.desktop /usr/share/wayland-sessions/", check=False)
            run_cmd_live("sudo mkdir -p /usr/share/xdg-terminal-exec")
            run_cmd_live("sudo cp default/xdg-terminal-exec/hyprland-xdg-terminals.list /usr/share/xdg-terminal-exec/", check=False)
            
            run_cmd_live("sudo bash -c 'echo \"export OMARCHY_PATH=/usr/share/omarchy\" > /etc/profile.d/omarchy.sh'")
            run_cmd_live("sudo chmod +x /etc/profile.d/omarchy.sh")
            
            # Copiado acelerado mediante Python nativo (shutil)
            shutil.copytree("config", os.path.expanduser("~/.config"), dirs_exist_ok=True)
    
            # Auto-configurar teclado leyendo localectl
            try:
                res = subprocess.run(["localectl", "status"], capture_output=True, text=True)
                kb_layout = "us"
                for line in res.stdout.splitlines():
                    if "X11 Layout:" in line:
                        kb_layout = line.split(":")[1].strip()
                        break
                
                # Reemplazar teclado en la configuración de Hyprland (Omarchy)
                omarchy_input = os.path.expanduser("~/.config/hypr/input.lua")
                if os.path.exists(omarchy_input):
                    with open(omarchy_input, "r") as f:
                        content = f.read()
                    content = content.replace('-- hl.config({', 'hl.config({', 1)
                    content = content.replace('--   input = {', '  input = {', 1)
                    content = content.replace('--     kb_layout = "us,dk,eu",', f'    kb_layout = "{kb_layout}",', 1)
                    content = content.replace('--   },\n-- })', '  },\n})', 1)
                    with open(omarchy_input, "w") as f:
                        f.write(content)
            except Exception:
                pass
                        
            shutil.copytree("bin", os.path.expanduser("~/.local/bin"), dirs_exist_ok=True)
            shutil.copytree("themes", os.path.expanduser("~/.local/share/themes"), dirs_exist_ok=True)
            run_cmd_live("chmod +x ~/.local/bin/*", check=False)
        
        has_cachyos_settings = any("cachyos-" in pkg and "-settings" in pkg for pkg in pkgs)
        if has_cachyos_settings:
            log_lines.append("[yellow]Aplicando estética de CachyOS desde /etc/skel...[/yellow]")
            run_cmd_live("if [ -d /etc/skel/.config ]; then cp -rn /etc/skel/.config/* ~/.config/ 2>/dev/null || true; fi", check=False)
            run_cmd_live("if [ -d /etc/skel/.local ]; then cp -rn /etc/skel/.local/* ~/.local/ 2>/dev/null || true; fi", check=False)
            run_cmd_live(f"sudo chown -R $USER:$USER ~/.config ~/.local 2>/dev/null", check=False)
        
        if install_plymouth_flag:
            progress.update(t_config, description=f"[yellow]Configurando Pantalla de Arranque ({install_plymouth_theme_name})...", advance=5)
            setup_plymouth_bootloader(has_nvidia, install_plymouth_theme_name)
        
        progress.update(t_config, description="[yellow]Desplegando Selector TTY1...", advance=5)
        
        # --- Configurar Sesiones en TTY Pura (Eliminación Total de Display Managers) ---
        run_cmd_live("sudo mkdir -p /etc/systemd/system/greetd.service.d", check=False)
        with open("/tmp/plymouth-fix.conf", "w") as f:
            f.write("[Service]\nExecStartPre=-/usr/bin/plymouth quit\n")
        run_cmd_live("sudo mv /tmp/plymouth-fix.conf /etc/systemd/system/greetd.service.d/plymouth-fix.conf", check=False)


        # --- Configurar Sesiones Híbridas ---
        if force_tty:
            # 1. Arte ASCII para TTY1 (Antes de Loguearse)
            issue_omarchy = """\\e[2J\\e[H

\\e[38;2;0;255;255m╭──────────────────────────────────────────────────────────────────────────────────────╮\\e[0m
\\e[38;2;0;230;255m│\\e[0m \\e[38;2;0;230;255m ██╗  ██╗ ██████╗ ██╗  ██╗    ███████╗████████╗██╗   ██╗██████╗ ██╗ ██████╗ ███████╗\\e[0m \\e[38;2;0;230;255m│\\e[0m
\\e[38;2;0;200;255m│\\e[0m \\e[38;2;0;200;255m ╚██╗██╔╝██╔════╝ ██║  ██║    ██╔════╝╚══██╔══╝██║   ██║██╔══██╗██║██╔═══██╗██╔════╝\\e[0m \\e[38;2;0;200;255m│\\e[0m
\\e[38;2;150;0;255m│\\e[0m \\e[38;2;150;0;255m  ╚███╔╝ ███████╗ ███████║    ███████╗   ██║   ██║   ██║██║  ██║██║██║   ██║███████╗\\e[0m \\e[38;2;150;0;255m│\\e[0m
\\e[38;2;255;0;200m│\\e[0m \\e[38;2;255;0;200m  ██╔██╗ ██╔═══██╗╚════██║    ╚════██║   ██║   ██║   ██║██║  ██║██║██║   ██║╚════██║\\e[0m \\e[38;2;255;0;200m│\\e[0m
\\e[38;2;255;0;100m│\\e[0m \\e[38;2;255;0;100m ██╔╝ ██╗╚██████╔╝     ██║    ███████║   ██║   ╚██████╔╝██████╔╝██║╚██████╔╝███████║\\e[0m \\e[38;2;255;0;100m│\\e[0m
\\e[38;2;255;0;50m╰──────────────────────────────────────────────────────────────────────────────────────╯\\e[0m
\\e[1;36m           D   A   S   H   B   O   A   R   D       //       C   O   R   E\\e[0m

\\e[1;32m>>> X64 STUDIOS DASHBOARD (PANEL DE CONTROL TTY1) <<<\\e[0m
\\e[1;37mBienvenido. Si estás viendo esta pantalla, significa que el sistema no inició
el entorno gráfico automáticamente (muy común en hardware gráfico Legacy).

¡Pero no te preocupes! Este es tu \\e[1;36mCentro de Mando Seguro\\e[1;37m.
Ingresa tus credenciales aquí abajo para desplegar el selector de sesiones. Desde allí podrás 
lanzar tus escritorios (Hyprland, KDE, etc.) o usar herramientas avanzadas de diagnóstico.\\e[0m

\\e[38;2;0;255;150m> INGRESA TU USUARIO Y CONTRASEÑA PARA CONTINUAR:\\e[0m

"""
            with open("/tmp/issue.omarchy", "w", encoding="utf-8") as f:
                f.write(issue_omarchy)
            run_cmd_live("sudo mv /tmp/issue.omarchy /etc/issue.omarchy", check=False)
            run_cmd_live("sudo bash -c 'echo -e \"\\\\S \\\\r (\\\\l)\\\\n\" > /etc/issue'", check=False)
        
            run_cmd_live("sudo mkdir -p /etc/systemd/system/getty@tty1.service.d/", check=False)
            getty_override = "[Service]\nExecStart=\nExecStart=-/sbin/agetty -o '-p -- \\u' --noclear --issue-file /etc/issue.omarchy %I $TERM\n"
            with open("/tmp/issue.conf", "w") as f:
                f.write(getty_override)
            run_cmd_live("sudo mv /tmp/issue.conf /etc/systemd/system/getty@tty1.service.d/issue.conf", check=False)
            run_cmd_live("sudo systemctl daemon-reload", check=False)

            # 2. Selector Interactivo de Entornos para Fish (Después de Loguearse)
            fish_selector = """if status is-login
        if test (tty) = /dev/tty1
            set border_color "\\e[38;2;0;255;255m"
            set text_color "\\e[38;2;0;230;255m"
            set bat_path (ls /sys/class/power_supply/BAT* 2>/dev/null | head -n 1)
            set bat_pct "N/A"
            if test -n "$bat_path" -a -f "$bat_path/capacity"
                set bat_pct (cat $bat_path/capacity)
                if test $bat_pct -lt 20
                    set border_color "\\e[38;2;255;50;50m"
                    set text_color "\\e[38;2;255;100;100m"
                end
            end

            set current_time (date '+%Y-%m-%d %H:%M:%S')
            set ip_addr (ip route get 1.1.1.1 2>/dev/null | awk '{print $7}')
            if test -z "$ip_addr"
                set ip_addr "Offline"
            end
            set mem_used (free -m | awk '/Mem:/ {print $3}')
            set mem_total (free -m | awk '/Mem:/ {print $2}')
            
            set temp_raw (cat /sys/class/thermal/thermal_zone0/temp 2>/dev/null)
            set cpu_temp "N/A"
            if test -n "$temp_raw"
                set cpu_temp (math "$temp_raw / 1000")"°C"
            end

            set os_name (cat /etc/os-release | grep "PRETTY_NAME" | cut -d '=' -f 2 | tr -d '"')
            set kernel_ver (uname -r)
            set host_node (hostname)

            echo -e "\\n$border_color────────────────────────────────────────────────────────────\\e[0m"
            echo -e " \\e[1;37m X64 MEGA DASHBOARD // TELEMETRY\\e[0m"
            echo -e "$border_color────────────────────────────────────────────────────────────\\e[0m"
            echo -e " \\e[1;36m[OS]\\e[0m     $os_name"
            echo -e " \\e[1;35m[KERNEL]\\e[0m $kernel_ver"
            echo -e " \\e[1;36m[NODE]\\e[0m   $host_node"
            echo -e " \\e[1;33m[TIME]\\e[0m   $current_time"
            echo -e " \\e[1;34m[IP]\\e[0m     $ip_addr"
            echo -e " \\e[1;32m[RAM]\\e[0m    $mem_used MB / $mem_total MB"
            echo -e " \\e[1;31m[TEMP]\\e[0m   $cpu_temp"
            echo -e " \\e[1;32m[BAT]\\e[0m    $bat_pct%"
            echo -e "$border_color────────────────────────────────────────────────────────────\\e[0m"
            echo -e "$border_color> INGRESA EL NÚMERO DE LA SESIÓN:\\e[0m\\n"

            set idx 1
            set options
            set cmds
        
    """
            for item in menu_data[0]["items"]:
                if item.get("selected"):
                    label = item["label"]
                    if "Omarchy Oficial" in label:
                        fish_selector += """        if type -q Hyprland
                echo " [$idx] Hyprland (Omarchy Oficial)"
                set -a options $idx
                set -a cmds "exec Hyprland"
                set idx (math $idx + 1)
            end\n"""

                    elif "KDE" in label:
                        fish_selector += """        if type -q startplasma-wayland
                echo " [$idx] KDE Plasma"
                set -a options $idx
                set -a cmds "exec dbus-run-session startplasma-wayland"
                set idx (math $idx + 1)
            end\n"""

                    elif "Niri" in label:
                        fish_selector += """        if type -q niri-session
                echo " [$idx] Niri"
                set -a options $idx
                set -a cmds "exec dbus-run-session niri"
                set idx (math $idx + 1)
            end\n"""
                    elif "Cinnamon" in label:
                        fish_selector += """        if type -q cinnamon-session
                echo " [$idx] Cinnamon"
                set -a options $idx
                set -a cmds "exec dbus-run-session startx /usr/bin/cinnamon-session"
                set idx (math $idx + 1)
            end\n"""

            fish_selector += """
            echo ""
            echo -e " \\e[1;36m>> HERRAMIENTAS DE RESCATE <<\\e[0m"
            echo " [U] Actualizar Sistema (Pacman/AUR)"
            echo " [L] Limpieza Profunda de Caché"
            echo " [N] Diagnóstico de Red"
            echo " [E] Escáner de Errores (Health Check)"
            echo " [K] Reparar Pacman (Llaves/Mirrors)"
            echo ""
            echo " [R] Reiniciar el Sistema"
            echo " [A] Apagar el Sistema"
            echo " [C] Consola Pura (Mantenimiento Avanzado)"
            echo ""

            while true
                read -p 'echo -n "❯ Elige una opción: "' choice
                
                if test "$choice" = "C" -o "$choice" = "c"
                    break
                else if test "$choice" = "R" -o "$choice" = "r"
                    systemctl reboot
                    break
                else if test "$choice" = "A" -o "$choice" = "a"
                    systemctl poweroff
                    break
                else if test "$choice" = "U" -o "$choice" = "u"
                    clear
                    echo -e "\\e[1;32mIniciando actualización del sistema...\\e[0m"
                    if type -q paru
                        paru -Syu
                    else
                        sudo pacman -Syu
                    end
                    echo -e "\\n\\e[1;32mActualización completada. Presiona Enter para volver.\\e[0m"
                    read
                    exec fish -l
                else if test "$choice" = "L" -o "$choice" = "l"
                    clear
                    echo -e "\\e[1;33mEjecutando limpieza profunda...\\e[0m"
                    echo "Destruyendo descargas parciales y corruptas (error fd 7)..."
                    sudo rm -f /var/cache/pacman/pkg/*.part
                    sudo rm -f /var/cache/pacman/pkg/*.download
                    echo "Vaciando caché de paquetes viejos..."
                    sudo pacman -Sc --noconfirm
                    if type -q paru
                        paru -Sc --noconfirm
                    end
                    sudo journalctl --vacuum-time=1w
                    echo -e "\\n\\e[1;32mLimpieza completada. Presiona Enter para volver.\\e[0m"
                    read
                    exec fish -l
                else if test "$choice" = "N" -o "$choice" = "n"
                    clear
                    echo -e "\\e[1;36m>> DIAGNÓSTICO DE RED <<\\e[0m"
                    echo -e "\\n--- Interfaces de Red ---"
                    ip addr
                    echo -e "\\n--- Prueba de Ping a Google (8.8.8.8) ---"
                    ping -c 4 8.8.8.8
                    echo -e "\\n\\e[1;33mPresiona Enter para volver al menú.\\e[0m"
                    read
                    exec fish -l
                else if test "$choice" = "E" -o "$choice" = "e"
                    clear
                    echo -e "\\e[1;31m>> ESCÁNER DE ERRORES CRÍTICOS (Último Arranque) <<\\e[0m"
                    echo -e "\\e[1;33m[!] ADVERTENCIA: Usa las flechas para leer. Presiona la letra 'Q' para salir de los logs.\\e[0m"
                    sleep 2
                    sudo journalctl -p 3 -xb
                    echo -e "\\n\\e[1;33mPresiona Enter para volver al menú.\\e[0m"
                    read
                    exec fish -l
                else if test "$choice" = "K" -o "$choice" = "k"
                    clear
                    echo -e "\\e[1;32m>> REPARANDO PACMAN (Llaves y Mirrors) <<\\e[0m"
                    echo -e "\\e[1;33mRefrescando llaves de cifrado... esto puede tardar un poco.\\e[0m"
                    sudo pacman-key --refresh-keys
                    echo -e "\\e[1;33mOptimizando servidores espejo (rate-mirrors)...\\e[0m"
                    if type -q rate-mirrors
                        rate-mirrors arch | sudo tee /etc/pacman.d/mirrorlist
                    else
                        echo "Instalando rate-mirrors temporalmente..."
                        sudo pacman -S --noconfirm rate-mirrors
                        rate-mirrors arch | sudo tee /etc/pacman.d/mirrorlist
                    end
                    echo -e "\\n\\e[1;32mReparación completada. Presiona Enter para volver.\\e[0m"
                    read
                    exec fish -l
                end
            
                set list_idx 0
                for i in (seq (count $options))
                    if test "$choice" = "$options[$i]"
                        set list_idx $i
                        break
                    end
                end
            
                if test $list_idx -gt 0
                    eval $cmds[$list_idx]
                    break
                else
                    echo -e "\\e[31mOpción inválida.\\e[0m"
                end
            end
        end
    end
    """
            run_cmd_live("mkdir -p ~/.config/fish/conf.d", check=False)
            run_cmd_live("rm -f ~/.config/fish/conf.d/hyprland_autostart.fish", check=False)
            with open(os.path.expanduser("~/.config/fish/conf.d/omarchy_selector.fish"), "w") as f:
                f.write(fish_selector)
        else:
            run_cmd_live("rm -f ~/.config/fish/conf.d/omarchy_selector.fish", check=False)
            run_cmd_live("sudo rm -f /etc/systemd/system/getty@tty1.service.d/issue.conf", check=False)
            run_cmd_live("sudo rm -f /etc/issue.omarchy", check=False)
            run_cmd_live("sudo systemctl daemon-reload", check=False)

        # --- Batch Shelling para Servicios y Entornos ---
        progress.update(t_config, description="[yellow]Aplicando configuraciones finales (Batch Shell)...", advance=10)
        services_script = "#!/bin/bash\n"
        
        is_omarchy_oficial = False
        for item in menu_data[0]["items"]:
            if item.get("selected") and "Omarchy Oficial" in item["label"]:
                is_omarchy_oficial = True
                break

        if not force_tty:
            if is_omarchy_oficial:
                actual_user = os.environ.get("USER", "root")
                services_script += "mkdir -p /usr/share/sddm/themes/omarchy /etc/sddm.conf.d /var/lib/sddm\n"
                services_script += "cp -r default/sddm/omarchy/* /usr/share/sddm/themes/omarchy/ 2>/dev/null\n"
                services_script += "echo -e \"[Theme]\\nCurrent=omarchy\" > /etc/sddm.conf.d/omarchy.conf\n"
                services_script += f"echo -e \"[Last]\\nSession=/usr/share/wayland-sessions/omarchy.desktop\\nUser={actual_user}\" > /var/lib/sddm/state.conf\n"
                services_script += "chown -R sddm:sddm /var/lib/sddm\n"
            else:
                services_script += "rm -f /etc/sddm.conf.d/omarchy.conf\n"

            services_script += "systemctl disable greetd.service 2>/dev/null\n"
            services_script += "systemctl disable getty@tty1.service 2>/dev/null\n"
            services_script += "mkdir -p /etc/sddm.conf.d\n"
            services_script += "echo -e \"[General]\\nDisplayServer=x11\" > /etc/sddm.conf.d/10-x11.conf\n"
            services_script += "systemctl enable sddm.service --now\n"
        else:
            services_script += "systemctl disable sddm.service 2>/dev/null\n"
            services_script += "systemctl disable greetd.service 2>/dev/null\n"
            services_script += "systemctl enable getty@tty1.service --now\n"

        services_script += "systemctl enable bluetooth.service\n"
        services_script += "systemctl enable systemd-oomd.service\n"
        
        if "ananicy-cpp" in user_choices["packages"]:
            services_script += "systemctl enable ananicy-cpp.service\n"
        if "zram-generator" in user_choices["packages"]:
            services_script += "systemctl daemon-reload\n"
            services_script += "systemctl restart systemd-zram-setup@zram0.service\n"
        if "uksmd" in user_choices["packages"]:
            services_script += "systemctl enable uksmd.service\n"
        if "irqbalance" in user_choices["packages"]:
            services_script += "systemctl enable irqbalance.service\n"
        if "cups" in user_choices["packages"]:
            services_script += "systemctl enable cups.service\n"
            
        with open("/tmp/omarchy-services.sh", "w") as f:
            f.write(services_script)
        run_cmd_live("sudo bash /tmp/omarchy-services.sh", check=False)
        
        progress.update(t_config, description="[yellow]Aplicando Diseño y Tema...", advance=20)
        if install_hyprland and user_choices["theme"] == "Tokyo Night":
            run_cmd_live("export OMARCHY_PATH=/usr/share/omarchy && export OMARCHY_THEME_HEADLESS=1 && /usr/share/omarchy/bin/omarchy-theme-set 'Tokyo Night'", check=False)
        
        progress.update(t_final, description="[yellow]Purgando caché de Pacman...", advance=10)
        run_cmd_live("sudo pacman -Scc --noconfirm", check=False)
        
        progress.update(t_config, description="[green]Sistema Listo", completed=100)
        
    except Exception as e:
        install_error = str(e)
    finally:
        install_done = True
        current_state = "error" if install_error else "done"


with open(LOG_FILE, "w") as f:
    f.write("=== Inicio de Instalación X64-Omarchy (Mega Dashboard) ===\n")

live_instance = None

try:
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    
    import fcntl
    fl = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
    
    installer_started = False
    
    with Live(update_ui(), auto_refresh=False, screen=True) as live:
        tty.setcbreak(fd)
        
        while not install_done:
            if current_state == "menu":
                r, _, _ = select.select([sys.stdin], [], [], 0.25)
                if r:
                    try:
                        chunk = os.read(fd, 10)
                        if chunk:
                            ch = chunk.decode('utf-8', errors='ignore')
                            if '\x1b[A' in ch or '\x1bOA' in ch:
                                if active_pane == "left":
                                    cat_idx = max(0, cat_idx - 1)
                                    item_idx = 0
                                else:
                                    item_idx = max(0, item_idx - 3)
                            elif '\x1b[B' in ch or '\x1bOB' in ch:
                                if active_pane == "left":
                                    cat_idx = min(len(menu_data) - 1, cat_idx + 1)
                                    item_idx = 0
                                else:
                                    item_idx = min(len(menu_data[cat_idx]["items"]) - 1, item_idx + 3)
                            elif '\x1b[C' in ch or '\x1bOC' in ch:
                                if active_pane == "left":
                                    active_pane = "right"
                                else:
                                    item_idx = min(len(menu_data[cat_idx]["items"]) - 1, item_idx + 1)
                            elif '\x1b[D' in ch or '\x1bOD' in ch:
                                if active_pane == "right":
                                    if item_idx % 3 == 0:
                                        active_pane = "left"
                                    else:
                                        item_idx = max(0, item_idx - 1)
                            elif ' ' in ch:
                                if active_pane == "right":
                                    category = menu_data[cat_idx]
                                    item = category["items"][item_idx]
                                    if item["type"] == "toggle":
                                        if "Entornos" in category["cat"]:
                                            for i in category["items"]:
                                                i["selected"] = False
                                            item["selected"] = True
                                        else:
                                            item["selected"] = not item.get("selected", False)
                            elif '\r' in ch or '\n' in ch:
                                if active_pane == "right":
                                    item = menu_data[cat_idx]["items"][item_idx]
                                    if item["type"] == "action":
                                        for c in menu_data:
                                            for i in c["items"]:
                                                if i.get("selected"):
                                                    user_choices["packages"].extend(i.get("pkg", []))
                                        
                                        current_state = "plymouth_modal"
                                        plymouth_modal_idx = 0
                                    else:
                                        category = menu_data[cat_idx]
                                        if "Entornos" in category["cat"]:
                                            for i in category["items"]:
                                                i["selected"] = False
                                            item["selected"] = True
                                        else:
                                            item["selected"] = not item.get("selected", False)
                                else:
                                    active_pane = "right"
                            elif '\x03' in ch:
                                install_error = "Instalación abortada por el usuario (Ctrl+C)."
                                install_done = True
                                break
                    except BlockingIOError:
                        pass
            elif current_state == "plymouth_modal":
                r, _, _ = select.select([sys.stdin], [], [], 0.05)
                if r:
                    try:
                        chunk = os.read(fd, 10)
                        if chunk:
                            ch = chunk.decode('utf-8', errors='ignore')
                            if '\x1b[C' in ch or '\x1bOC' in ch:
                                plymouth_modal_idx = 1
                            elif '\x1b[D' in ch or '\x1bOD' in ch:
                                plymouth_modal_idx = 0
                            elif '\r' in ch or '\n' in ch:
                                if plymouth_modal_idx == 0:
                                    user_choices["packages"].append("plymouth")
                                    install_plymouth_flag = True
                                else:
                                    install_plymouth_flag = False
                                
                                theme_name = "omarchy"
                                for c in menu_data:
                                    if "Entornos" in c["cat"]:
                                        for i in c["items"]:
                                            if i.get("selected") and "X64 Studios" in i["label"]:
                                                theme_name = "x64-studios"
                                                break
                                install_plymouth_theme_name = theme_name
                                
                                current_state = "transition"
                                transition_text = "Cargando Secuencia de Lanzamiento..."
                    except BlockingIOError:
                        pass
            elif current_state == "transition":
                # Handle transition animation inside the main thread loop
                live.update(update_ui())
                live.refresh()
                time.sleep(0.7)
                transition_text = "Verificando Sistemas Vitales..."
                live.update(update_ui())
                live.refresh()
                time.sleep(0.7)
                transition_text = "Desplegando Motor X64-Omarchy..."
                live.update(update_ui())
                live.refresh()
                time.sleep(0.8)
                current_state = "working"
            elif current_state == "error" and error_prompt:
                r, _, _ = select.select([sys.stdin], [], [], 0.25)
                if r:
                    try:
                        chunk = os.read(fd, 10)
                        if chunk:
                            ch = chunk.decode('utf-8', errors='ignore')
                            if '\x1b[C' in ch or '\x1bOC' in ch:
                                error_idx = min(2, error_idx + 1)
                            elif '\x1b[D' in ch or '\x1bOD' in ch:
                                error_idx = max(0, error_idx - 1)
                            elif '\r' in ch or '\n' in ch:
                                error_response = ["Reintentar", "Ignorar", "Abortar"][error_idx]
                                # Note: the installer_worker will reset error_prompt and current_state
                    except BlockingIOError:
                        pass
            elif current_state == "working" and not installer_started:
                start_time = time.time()
                installer_started = True
                worker = threading.Thread(target=installer_worker, daemon=True)
                worker.start()
            
            # --- UPDATE UI SYNCHRONOUSLY ---
            live.update(update_ui())
            live.refresh()
            
            if current_state != "menu" and current_state != "transition":
                time.sleep(0.25)
                
        end_time = time.time()
        live.update(update_ui())
        time.sleep(2)

except KeyboardInterrupt:
    install_error = "Instalación abortada por el usuario (Ctrl+C)."
    install_done = True
finally:
    termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

print("\n")
if not install_error:
    time_taken = end_time - start_time if start_time else 0
    mins, secs = divmod(time_taken, 60)
    
    report = Table(title="[bold cyan]Reporte Final de Metamorfosis X64[/bold cyan]", box=None, expand=True)
    report.add_column("Métrica", style="cyan")
    report.add_column("Detalle", style="white")
    
    report.add_row("Tiempo de Instalación", f"{int(mins)}m {int(secs)}s")
    report.add_row("Tema Base", user_choices["theme"])
    report.add_row("Software Extra Elegido", f"{len(user_choices['packages'])} paquetes")
    if len(user_choices["packages"]) > 0:
        report.add_row("Lista de Software", ", ".join(user_choices["packages"]))
    report.add_row("Archivo de Log", f"[dim]{LOG_FILE}[/dim]")
    
    console.print(Panel(report, border_style="green", title="[bold green]¡Sistema Listo![/bold green]"))
    
    try:
        termios.tcflush(fd, termios.TCIFLUSH)
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        fcntl.fcntl(fd, fcntl.F_SETFL, fl)
    except Exception:
        pass
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
