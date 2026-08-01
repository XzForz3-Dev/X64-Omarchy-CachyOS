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
                        # Mitigación I/O: Solo enviamos al UI render las líneas importantes o espaciadas
                        if "error" in line_clean.lower() or "warning" in line_clean.lower() or len(line_clean) > 10:
                            safe_line = escape(line_clean)
                            log_lines.append(f"[dim white]{safe_line}[/dim white]")
                        
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

    elif current_state == "error" and error_prompt:
        global ui_transitioned
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



def setup_plymouth_bootloader(has_nvidia_gpu=False):
    log_lines.append("[yellow]Aplicando tema de Plymouth...[/yellow]")
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
        progress.update(t_health, description="[yellow]Verificando Red...", advance=30)
        run_cmd_live("ping -c 1 archlinux.org")
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
        if os.path.exists("install/omarchy-base.packages"):
            with open("install/omarchy-base.packages") as f1:
                pkgs.extend(f1.read().splitlines())
        if os.path.exists("install/omarchy-other.packages"):
            with open("install/omarchy-other.packages") as f2:
                pkgs.extend(f2.read().splitlines())
        
        # Batch de paquetes críticos de sistema
        pkgs.extend(["plymouth", "xorg-xinit", "xorg-server"])
        pkgs.extend(user_choices["packages"])
        pkgs = list(set(pkgs))
        pkg_str = " ".join([p for p in pkgs if p and not p.startswith('#')])
        
        chk = subprocess.run(f"pacman -T {pkg_str}", shell=True, stdout=subprocess.PIPE, text=True)
        if chk.returncode != 0:
            missing_pkgs = [p for p in chk.stdout.splitlines()]
            progress.update(t_pkg, description="[cyan]Descargando e Instalando Paquetes (Puede tardar varios minutos)...", advance=40)
            run_cmd_live("sudo pacman -Rdd --noconfirm jack2", check=False)
            run_cmd_live("sudo pacman -Rdd --noconfirm cachyos-hyprland-settings cachyos-desktop-settings", check=False)

            run_cmd_live(f"sudo pacman -S --noconfirm {' '.join(missing_pkgs)}")
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
        run_cmd_live("sudo cp default/wayland-sessions/*.desktop /usr/share/wayland-sessions/", check=False)
        run_cmd_live("sudo mkdir -p /usr/share/xdg-terminal-exec")
        run_cmd_live("sudo cp default/xdg-terminal-exec/hyprland-xdg-terminals.list /usr/share/xdg-terminal-exec/", check=False)
        
        run_cmd_live("sudo bash -c 'echo \"export OMARCHY_PATH=/usr/share/omarchy\" > /etc/profile.d/omarchy.sh'")
        run_cmd_live("sudo chmod +x /etc/profile.d/omarchy.sh")
        
        # Copiado acelerado mediante Python nativo (shutil)
        shutil.copytree("config", os.path.expanduser("~/.config"), dirs_exist_ok=True)

                    
        shutil.copytree("bin", os.path.expanduser("~/.local/bin"), dirs_exist_ok=True)
        shutil.copytree("themes", os.path.expanduser("~/.local/share/themes"), dirs_exist_ok=True)
        run_cmd_live("chmod +x ~/.local/bin/*", check=False)
        
        progress.update(t_config, description="[yellow]Configurando Pantalla de Arranque (Plymouth)...", advance=5)
        setup_plymouth_bootloader(has_nvidia)
        
        progress.update(t_config, description="[yellow]Desplegando Selector TTY1...", advance=5)
        
        # --- Configurar Sesiones en TTY Pura (Eliminación Total de Display Managers) ---
        run_cmd_live("sudo mkdir -p /etc/systemd/system/greetd.service.d", check=False)
        with open("/tmp/plymouth-fix.conf", "w") as f:
            f.write("[Service]\nExecStartPre=-/usr/bin/plymouth quit\n")
        run_cmd_live("sudo mv /tmp/plymouth-fix.conf /etc/systemd/system/greetd.service.d/plymouth-fix.conf", check=False)

        # --- Configurar Sesiones Híbridas ---
        if is_legacy_nvidia:
            # 1. Arte ASCII para TTY1 (Antes de Loguearse)
            issue_omarchy = """\\e[2J\\e[H

\\e[38;2;0;255;255m╭───────────────────────────────────────────────────────────────────╮\\e[0m
\\e[38;2;0;230;255m│\\e[0m  \\e[38;2;0;230;255m ██████╗ ███╗   ███╗ █████╗ ██████╗  ██████╗██╗  ██╗██╗   ██╗\\e[0m \\e[38;2;0;230;255m│\\e[0m
\\e[38;2;0;200;255m│\\e[0m  \\e[38;2;0;200;255m██╔═══██╗████╗ ████║██╔══██╗██╔══██╗██╔════╝██║  ██║╚██╗ ██╔╝\\e[0m \\e[38;2;0;200;255m│\\e[0m
\\e[38;2;150;0;255m│\\e[0m  \\e[38;2;150;0;255m██║   ██║██╔████╔██║███████║██████╔╝██║     ███████║ ╚████╔╝\\e[0m  \\e[38;2;150;0;255m│\\e[0m
\\e[38;2;255;0;200m│\\e[0m  \\e[38;2;255;0;200m██║   ██║██║╚██╔╝██║██╔══██║██╔══██╗██║     ██╔══██║  ╚██╔╝\\e[0m   \\e[38;2;255;0;200m│\\e[0m
\\e[38;2;255;0;100m│\\e[0m  \\e[38;2;255;0;100m╚██████╔╝██║ ╚═╝ ██║██║  ██║██║  ██║╚██████╗██║  ██║   ██║\\e[0m     \\e[38;2;255;0;100m│\\e[0m
\\e[38;2;255;0;50m╰───────────────────────────────────────────────────────────────────╯\\e[0m

\\e[1;36m[\\e[0m \\e[1;37m\\S \\m\\e[0m \\e[1;36m]\\e[0m   \\e[1;35m[\\e[0m \\e[1;37m\\r\\e[0m \\e[1;35m]\\e[0m
\\e[1;36m[\\e[0m \\e[1;37m\\n (\\l)\\e[0m \\e[1;36m]\\e[0m   \\e[1;35m[\\e[0m \\e[1;37m\\d - \\t\\e[0m \\e[1;35m]\\e[0m

\\e[1;32m>>> MODO GRÁFICO (PORTAL PRINCIPAL) <<<\\e[0m
\\e[1;37mEstás en la \\e[1;33mTTY1\\e[1;37m. Ingresa tu usuario y contraseña aquí para 
entrar al selector interactivo de escritorios de Omarchy.\\e[0m

\\e[38;2;0;255;150m> INGRESA TUS CREDENCIALES ABAJO:\\e[0m

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

        # 2. Selector Interactivo de Entornos para Fish (Después de Loguearse)
        fish_selector = """if status is-login
    if test (tty) = /dev/tty1
        echo -e "\\e[1;32m>>> SELECTOR DE ESCRITORIOS X64-OMARCHY <<<\\e[0m"
        set idx 1
        set options
        set cmds
        
        if type -q Hyprland
            echo " [$idx] Hyprland (Omarchy Official)"
            set -a options $idx
            set -a cmds "exec Hyprland"
            set idx (math $idx + 1)
            
        if type -q startplasma-wayland
            echo " [$idx] KDE Plasma (X64 Studios Edition)"
            set -a options $idx
            set -a cmds "exec dbus-run-session startplasma-wayland"
            set idx (math $idx + 1)
        end
        if type -q gnome-session
            echo " [$idx] GNOME"
            set -a options $idx
            set -a cmds "exec env XDG_SESSION_TYPE=wayland dbus-run-session gnome-shell --display-server --wayland"
            set idx (math $idx + 1)
        end
        if type -q cosmic-session
            echo " [$idx] Cosmic"
            set -a options $idx
            set -a cmds "exec cosmic-session"
            set idx (math $idx + 1)
        end
        if type -q niri-session
            echo " [$idx] Niri"
            set -a options $idx
            set -a cmds "exec niri-session"
            set idx (math $idx + 1)
        end
        if type -q cinnamon-session
            echo " [$idx] Cinnamon"
            set -a options $idx
            set -a cmds "exec dbus-run-session startx /usr/bin/cinnamon-session"
            set idx (math $idx + 1)
        end
        if type -q mate-session
            echo " [$idx] MATE"
            set -a options $idx
            set -a cmds "exec dbus-run-session startx /usr/bin/mate-session"
            set idx (math $idx + 1)
        end
        if type -q startxfce4
            echo " [$idx] Xfce4"
            set -a options $idx
            set -a cmds "exec startxfce4"
            set idx (math $idx + 1)
        end
        if type -q startlxqt
            echo " [$idx] LXQT"
            set -a options $idx
            set -a cmds "exec startx /usr/bin/startlxqt"
            set idx (math $idx + 1)
        end
        if type -q startlxde
            echo " [$idx] LXDE"
            set -a options $idx
            set -a cmds "exec startx /usr/bin/startlxde"
            set idx (math $idx + 1)
        end
        if type -q mangowm
            echo " [$idx] MangoWM"
            set -a options $idx
            set -a cmds "exec mangowm"
            set idx (math $idx + 1)
        end
        if type -q wayfire
            echo " [$idx] Wayfire"
            set -a options $idx
            set -a cmds "exec wayfire"
            set idx (math $idx + 1)
        end
        if type -q openbox-session
            echo " [$idx] Openbox"
            set -a options $idx
            set -a cmds "exec startx /usr/bin/openbox-session"
            set idx (math $idx + 1)
        end
        
        echo ""
        echo " [C] Consola Pura (Mantenimiento)"
        echo ""
        
        while true
            read -p 'echo -n "❯ Elige una opción: "' choice
            if test "$choice" = "C" -o "$choice" = "c"
                break
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

        # --- Batch Shelling para Servicios y Entornos ---
        progress.update(t_config, description="[yellow]Aplicando configuraciones finales (Batch Shell)...", advance=10)
        services_script = "#!/bin/bash\\n"
        
        if not is_legacy_nvidia:
            services_script += "mkdir -p /usr/share/sddm/themes/omarchy /etc/sddm.conf.d\\n"
            services_script += "cp -r default/sddm/omarchy/* /usr/share/sddm/themes/omarchy/ 2>/dev/null\\n"
            services_script += "echo -e \\\"[Theme]\\\\nCurrent=omarchy\\\" > /etc/sddm.conf.d/omarchy.conf\\n"
            services_script += "systemctl disable greetd.service 2>/dev/null\\n"
            services_script += "systemctl enable sddm.service --now\\n"
        else:
            services_script += "systemctl disable sddm.service 2>/dev/null\\n"
            services_script += "systemctl disable greetd.service 2>/dev/null\\n"
            services_script += "systemctl enable getty@tty1.service --now\\n"

        services_script += "systemctl enable bluetooth.service\\n"
        
        if "ananicy-cpp" in user_choices["packages"]:
            services_script += "systemctl enable ananicy-cpp.service\\n"
        if "zram-generator" in user_choices["packages"]:
            services_script += "systemctl daemon-reload\\n"
            services_script += "systemctl restart systemd-zram-setup@zram0.service\\n"
        if "uksmd" in user_choices["packages"]:
            services_script += "systemctl enable uksmd.service\\n"
        if "irqbalance" in user_choices["packages"]:
            services_script += "systemctl enable irqbalance.service\\n"
        if "cups" in user_choices["packages"]:
            services_script += "systemctl enable cups.service\\n"
            
        with open("/tmp/omarchy-services.sh", "w") as f:
            f.write(services_script)
        run_cmd_live("sudo bash /tmp/omarchy-services.sh", check=False)
        
        progress.update(t_config, description="[yellow]Aplicando Diseño y Tema...", advance=20)
        if user_choices["theme"] == "Tokyo Night":
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
                                    item = menu_data[cat_idx]["items"][item_idx]
                                    if item["type"] == "toggle":
                                        item["selected"] = not item.get("selected", False)
                            elif '\r' in ch or '\n' in ch:
                                if active_pane == "right":
                                    item = menu_data[cat_idx]["items"][item_idx]
                                    if item["type"] == "action":
                                        for c in menu_data:
                                            for i in c["items"]:
                                                if i.get("selected"):
                                                    user_choices["packages"].extend(i.get("pkg", []))
                                        
                                        current_state = "transition"
                                        # Set up transition animation state
                                        transition_text = "Cargando Secuencia de Lanzamiento..."
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
