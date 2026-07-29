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
    from rich.console import Console
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
menu_items = [
    {"label": "Tema: Tokyo Night", "type": "toggle", "selected": True, "pkg": []},
    {"label": "Drivers: NVIDIA (Privativo)", "type": "toggle", "selected": False, "pkg": ["nvidia-dkms", "nvidia-utils", "lib32-nvidia-utils", "nvidia-settings"]},
    {"label": "Navegador: Firefox", "type": "toggle", "selected": True, "pkg": ["firefox"]},
    {"label": "Navegador: Chromium", "type": "toggle", "selected": False, "pkg": ["chromium"]},
    {"label": "Navegador: Brave", "type": "toggle", "selected": False, "pkg": ["brave-bin"]},
    {"label": "Gaming: Paquete Jugador (Steam, Lutris, MangoHud)", "type": "toggle", "selected": False, "pkg": ["steam", "lutris", "mangohud", "gamemode"]},
    {"label": "Desarrollo: Paquete Creador (Docker, Git, VSCode)", "type": "toggle", "selected": False, "pkg": ["docker", "git", "code", "base-devel"]},
    {"label": "", "type": "separator"},
    {"label": "[ INICIAR METAMORFOSIS ]", "type": "action"}
]
current_menu_index = 0
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
 ▄▄▄▄▄▄▄  ▄▄▄ ▄▄ ▄▄▄ ▄▄ ▄  ▄▄▄▄▄▄▄ 
 █ ▄▄▄ █ ▄    █▀███▄▄ █▄   █ ▄▄▄ █ 
 █ ███ █ ██▀   ▀█▀ ▄▀▀▄▀▄▀ █ ███ █ 
 █▄▄▄▄▄█ █▀█▀█▀█▀█▀▄ █ ▄ ▄ █▄▄▄▄▄█ 
 ▄ ▄▄▄▄▄ ▀▀▀▀ ▄ █ ▄▀ ▄▀ ▀▀ ▄▄▄▄▄   
 ▀█▄▀█ ▄▀▄▀██▄  ▄▀ █▀▀▀ ▀▄ ▀▀▄▀█▀▀ 
 ▀▄██  ▄  █▄█▀ ▀█▀ ▄▄ ▀█▄█▄▀ ██▀▄▀ 
 █ ▀█▄ ▄▀ ▄▀ █ █▀▀█ ▄▀ ▄  ▄█  ▀██▀ 
 ▀▀▀▄ ▄▄▀ ▄█▀    ▀▄ ██▀▄▄▄█▀█▄ ▀ ▄ 
 ███ ▄ ▄▀▀█▄▄ ▀▄███  █▄ ▀▄ ▀█▄▀█▀▀ 
 ▄█▄ ██▄▄██▄   ▀▀█▀▀█▀▀▄ ▄█▀███▀ ▄ 
 █▀  ▀▄▄▀  ▀ █▀██▄▄█ ▄▀▀▀▀▄▀  █▄▄▀ 
 █ █▀▀█▄█   ▄▀ ██ ▄▀▀ ▀█▄███▄█▀█ ▀ 
 ▄▄▄▄▄▄▄ ▀████▀▀▄▄ ▄▀▄▄ ██ ▄ █ ██  
 █ ▄▄▄ █ █▀▀▄ ▄█▄  ▄▄███▀█▄▄▄██▀██ 
 █ ███ █ █▄▀▀█▀▄▀▀█▄ █ ▄▀▀▀▄▄▀█ ▀▀ 
 █▄▄▄▄▄█ ▄██▄▄ █ █▄██▀▀██▄ ▀▄▀▀▀▄  
"""

def get_static_logo():
    t1 = Text(logo_text.strip('\n') + "\n", style="bold cyan", justify="center")
    t2 = Text("GITHUB REPOSITORY\n", style="bold white", justify="center")
    t3 = Text(qr_text.strip('\n'), style="bold white", justify="center")
    
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
        text = "\n[bold cyan]Usa las FLECHAS para moverte. Presiona ESPACIO o ENTER para cambiar.[/bold cyan]\n\n"
        for i, item in enumerate(menu_items):
            cursor = "[bold yellow]➤[/bold yellow] " if i == current_menu_index else "  "
            if item["type"] == "separator":
                text += "\n"
            elif item["type"] == "action":
                style = "bold green reverse" if i == current_menu_index else "bold green"
                text += f"{cursor}[{style}]{item['label']}[/{style}]\n"
            else:
                if item["selected"]:
                    chk_box = "[bold green on black] ◉ ACTIVADO   [/bold green on black]"
                else:
                    chk_box = "[bold red on black] ◯ Desactivado[/bold red on black]"
                style = "bold white" if i == current_menu_index else "white"
                text += f"{cursor}{chk_box} [{style}]{item['label']}[/{style}]\n"
                
        layout["right"].update(Panel(Text.from_markup(text), title="[bold magenta]Configuración Pre-Vuelo[/bold magenta]", border_style=border_color))
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
    global current_menu_index, current_state
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
                    current_menu_index = max(0, current_menu_index - 1)
                    # Saltar separadores
                    if menu_items[current_menu_index]["type"] == "separator":
                        current_menu_index = max(0, current_menu_index - 1)
                elif ch == '\x1b[B': # Abajo
                    current_menu_index = min(len(menu_items) - 1, current_menu_index + 1)
                    if menu_items[current_menu_index]["type"] == "separator":
                        current_menu_index = min(len(menu_items) - 1, current_menu_index + 1)
                elif ch == ' ':
                    if menu_items[current_menu_index]["type"] != "action":
                        menu_items[current_menu_index]["selected"] = not menu_items[current_menu_index]["selected"]
                elif ch == '\r' or ch == '\n':
                    if menu_items[current_menu_index]["type"] == "action":
                        # Procesar selecciones
                        for item in menu_items:
                            if item.get("selected"):
                                user_choices["packages"].extend(item.get("pkg", []))
                                if "NVIDIA" in item["label"]:
                                    user_choices["drivers"] = "NVIDIA (Privativo)"
                        if "NVIDIA" not in user_choices["drivers"]:
                            user_choices["packages"].extend(["mesa", "lib32-mesa", "vulkan-radeon", "lib32-vulkan-radeon"])
                        
                        current_state = "transition"
                        break
                    else:
                        menu_items[current_menu_index]["selected"] = not menu_items[current_menu_index]["selected"]
                elif ch == '\x03': # Ctrl+C
                    global install_error, install_done
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
