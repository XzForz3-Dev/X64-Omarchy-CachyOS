import sys
import tty
import termios
import select
import time
import os
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.layout import Layout
from rich.align import Align
from rich.text import Text
from rich.table import Table
from rich import box
from rich.console import Group
from rich.markup import escape
import core.state as state
from core.hardware import get_sys_info

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
    t1 = Text("\n\n" + logo_text.strip('\n') + "\n", style="bold cyan", justify="center")
    if state.console.size.height > 50:
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
    border_color = "cyan"
    if state.current_state == "error":
        border_color = "red"
    elif state.current_state == "done":
        border_color = "green"
    elif state.current_state == "menu":
        border_color = "magenta"
    elif state.current_state == "transition":
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
    
    if state.current_state == "menu":
        items = state.menu_data[state.cat_idx]["items"]
        MAX_ROWS = 6
        
        current_row = state.item_idx // 3
        start_row = max(0, current_row - (MAX_ROWS // 2))
        end_row = start_row + MAX_ROWS
        
        total_rows = (len(items) + 2) // 3
        if end_row > total_rows:
            end_row = total_rows
            start_row = max(0, end_row - MAX_ROWS)
            
        start_idx = start_row * 3
        end_idx = end_row * 3
        
        visible_items = items[start_idx:end_idx]
        
        if items[0]["type"] == "action":
            is_active = (state.active_pane == "right")
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
                    
                is_active = (actual_i == state.item_idx and state.active_pane == "right")
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
        for i, c in enumerate(state.menu_data):
            if i == state.cat_idx:
                style = "bold cyan reverse" if state.active_pane == "left" else "bold cyan"
                prefix = "▶ " if state.active_pane == "left" else "  "
                cat_text += f"{prefix}[{style}]{c['cat']}[/{style}]\n\n"
            else:
                style = "dim white" if state.active_pane == "right" else "white"
                cat_text += f"  [{style}]{c['cat']}[/{style}]\n\n"
        
        nav_panel = Panel(
            Align.center(Text.from_markup("[bold cyan]NAVEGACIÓN:[/bold cyan] Flechas [bold yellow]← →[/bold yellow] cambian panel. Flechas [bold yellow]↑ ↓[/bold yellow] mueven selector. [bold yellow]ESPACIO[/bold yellow] alterna.", justify="center"), vertical="middle"),
            title=f"[bold magenta]Configuración Pre-Vuelo[/bold magenta]",
            border_style=border_color
        )
        
        cat_border = "cyan" if state.active_pane == "left" else "dim white"
        cat_text_obj = Text.from_markup(cat_text, no_wrap=True, overflow="crop")
        item_border = "green" if state.active_pane == "right" else "dim white"
        
        cat_panel = Panel(cat_text_obj, title="[bold cyan]Índice de Categorías[/bold cyan]", border_style=cat_border)
        grid_panel = Panel(Align.center(grid, vertical="middle"), title="[bold green]Opciones de Software[/bold green]", border_style=item_border)
        
        current_item = items[state.item_idx] if state.active_pane == "right" else state.menu_data[state.cat_idx]["items"][0]
        desc = current_item.get("desc", "Sin descripción detallada disponible.")
        
        warning_msg = ""
        if state.is_legacy_nvidia and "NVIDIA" in current_item["label"].upper():
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
        
        total_selected = sum(1 for c in state.menu_data for i in c["items"] if i.get("selected"))
        hud_text = Text.from_markup(f"[bold green]✓ Paquetes marcados para instalación:[/bold green] [bold white]{total_selected}[/bold white]   |   [dim]Presiona ENTER sobre [Iniciar Instalación] para proceder.[/dim]", style="white", justify="center")
        hud_panel = Panel(Align.center(hud_text, vertical="middle"), title="[bold cyan]ESTADO GLOBAL DEL SISTEMA[/bold cyan]", border_style="magenta", height=5, box=box.ROUNDED)
        
        main_layout = Layout()
        main_layout.split_column(
            Layout(nav_panel, size=3),
            Layout(menu_layout, ratio=1),
            Layout(hud_panel, size=5)
        )
        layout["right"].update(main_layout)

    elif state.current_state == "transition":
        layout["right"].update(Panel(Align.center(f"\n\n\n\n\n\n[bold yellow]{state.transition_text}[/bold yellow]"), title="[bold yellow]Inicializando Sistema...[/bold yellow]", border_style="yellow"))
    else:
        if not state.ui_transitioned:
            layout["right"].split_column(
                Layout(name="progress", ratio=1),
                Layout(name="matrix", ratio=2)
            )
            state.ui_transitioned = True
            
        layout["right"]["progress"].update(Panel(progress, title=f"[bold {border_color}]Progreso de Metamorfosis[/bold {border_color}]", border_style=border_color))
        matrix_text = "\n".join(list(state.log_lines)[-12:]) # Limitar estrictamente a 12 líneas
        matrix_obj = Text.from_markup(matrix_text, no_wrap=True, overflow="crop")
        layout["right"]["matrix"].update(Panel(matrix_obj, title="[bold yellow]The Matrix (Live Log)[/bold yellow]", border_style="yellow"))
        
    return layout

def keyboard_worker():
    time.sleep(0.5) # Esperar a que rich.Live inicialice la terminal
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        while state.current_state == "menu":
            # Forzar termios continuamente para vencer a rich.Live
            new_settings = termios.tcgetattr(fd)
            if new_settings[3] & (termios.ICANON | termios.ECHO):
                new_settings[3] = new_settings[3] & ~(termios.ICANON | termios.ECHO)
                termios.tcsetattr(fd, termios.TCSANOW, new_settings)
            if select.select([fd], [], [], 0.1)[0]:
                data = os.read(fd, 1024)
                if not data:
                    continue
                ch = data.decode('utf-8', errors='ignore')
                
                if '\x1b[A' in ch or '\x1bOA' in ch: # Arriba
                    if state.active_pane == "left":
                        state.cat_idx = max(0, state.cat_idx - 1)
                        state.item_idx = 0
                    else:
                        state.item_idx = max(0, state.item_idx - 3)
                elif '\x1b[B' in ch or '\x1bOB' in ch: # Abajo
                    if state.active_pane == "left":
                        state.cat_idx = min(len(state.menu_data) - 1, state.cat_idx + 1)
                        state.item_idx = 0
                    else:
                        state.item_idx = min(len(state.menu_data[state.cat_idx]["items"]) - 1, state.item_idx + 3)
                elif '\x1b[C' in ch or '\x1bOC' in ch: # Derecha
                    if state.active_pane == "left":
                        state.active_pane = "right"
                    else:
                        state.item_idx = min(len(state.menu_data[state.cat_idx]["items"]) - 1, state.item_idx + 1)
                elif '\x1b[D' in ch or '\x1bOD' in ch: # Izquierda
                    if state.active_pane == "right":
                        if state.item_idx % 3 == 0:
                            state.active_pane = "left"
                        else:
                            state.item_idx = max(0, state.item_idx - 1)
                elif ' ' in ch:
                    if state.active_pane == "right":
                        item = state.menu_data[state.cat_idx]["items"][state.item_idx]
                        if item["type"] == "toggle":
                            item["selected"] = not item.get("selected", False)
                elif '\r' in ch or '\n' in ch:
                    if state.active_pane == "right":
                        item = state.menu_data[state.cat_idx]["items"][state.item_idx]
                        if item["type"] == "action":
                            for c in state.menu_data:
                                for i in c["items"]:
                                    if i.get("selected"):
                                        state.user_choices["packages"].extend(i.get("pkg", []))
                                        if "NVIDIA" in i["label"]:
                                            state.user_choices["drivers"] = "NVIDIA (Privativo)"
                                            
                            if "NVIDIA" not in state.user_choices["drivers"]:
                                state.user_choices["packages"].extend(["mesa", "lib32-mesa", "vulkan-radeon", "lib32-vulkan-radeon", "vulkan-intel", "lib32-vulkan-intel"])
                            
                            state.current_state = "transition"
                            break
                        else:
                            item["selected"] = not item.get("selected", False)
                    else:
                        state.active_pane = "right"
                elif '\x03' in ch: # Ctrl+C
                    state.install_error = "Instalación abortada por el usuario (Ctrl+C)."
                    state.install_done = True
                    break
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        
    if state.current_state == "transition":
        state.transition_text = "Cargando Secuencia de Lanzamiento..."
        time.sleep(0.7)
        state.transition_text = "Verificando Sistemas Vitales..."
        time.sleep(0.7)
        state.transition_text = "Desplegando Motor X64-Omarchy..."
        time.sleep(0.8)
        state.current_state = "working"
