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
except ImportError:
    print("Fatal: python-rich not found. Please run the installer via x64-install.sh")
    sys.exit(1)

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
user_choices = {
    "theme": "Tokyo Night",
    "drivers": "Mesa (AMD/Intel Open Source)",
    "packages": []
}

def log(msg):
    time_str = datetime.now().strftime('%H:%M:%S')
    with open(LOG_FILE, "a") as f:
        f.write(f"[{time_str}] {msg}\n")
    log_lines.append(f"[bold blue][{time_str}][/bold blue] [bold cyan]{msg}[/bold cyan]")

def run_cmd_live(cmd, check=True):
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
        log(f"ERROR Fatal: El comando falló con código {process.returncode}")
        raise Exception(f"Comando fallido (revisa el log): {cmd}")
    return process.returncode

# --- Interactive Pre-Flight Phase ---
def gum_choose(title, options, multi=False):
    os.system("clear")
    print(f"\n\033[1;36m=== {title} ===\033[0m\n")
    if multi:
        print("\033[1;33mInstrucciones:\033[0m Usa ESPACIO para seleccionar varias opciones y ENTER para confirmar.\n")
    else:
        print("\033[1;33mInstrucciones:\033[0m Usa las FLECHAS para moverte y ENTER para confirmar.\n")
        
    cmd = ["gum", "choose"]
    if multi:
        cmd.append("--no-limit")
    cmd.extend(options)
    res = subprocess.run(cmd, stdout=subprocess.PIPE, text=True)
    return [x for x in res.stdout.strip().split('\n') if x]

def interactive_setup():
    global user_choices
    # Temas
    theme = gum_choose("Diseño Visual (Tema Base)", ["Tokyo Night", "Por defecto (CachyOS)"])
    user_choices["theme"] = theme[0] if theme else "Tokyo Night"
    
    # Drivers
    drivers = gum_choose("Controladores Gráficos (Drivers)", ["NVIDIA (Privativo)", "Mesa (AMD/Intel Open Source)"])
    user_choices["drivers"] = drivers[0] if drivers else "Mesa (AMD/Intel Open Source)"
    
    # Navegadores
    browsers = gum_choose("Software: Navegadores Web", ["firefox", "chromium", "brave-bin", "vivaldi"], multi=True)
    
    # Gaming
    gaming = gum_choose("Software: Paquetes Gaming", ["steam", "lutris", "mangohud", "gamemode", "wine"], multi=True)
    
    # Desarrollo
    dev = gum_choose("Software: Herramientas de Desarrollo", ["git", "docker", "code", "base-devel", "nodejs"], multi=True)
    
    user_choices["packages"] = browsers + gaming + dev
    
    # Añadir paquetes de drivers si es necesario
    if "NVIDIA" in user_choices["drivers"]:
        user_choices["packages"].extend(["nvidia-dkms", "nvidia-utils", "lib32-nvidia-utils", "nvidia-settings"])
    else:
        user_choices["packages"].extend(["mesa", "lib32-mesa", "vulkan-radeon", "lib32-vulkan-radeon"])

# --- System Info (Panel Izquierdo) ---
def get_sys_info():
    table = Table(show_header=False, expand=True, box=None)
    
    cpu = "Desconocido"
    try:
        with open("/proc/cpuinfo") as f:
            for line in f:
                if "model name" in line:
                    cpu = line.split(":")[1].strip()
                    break
    except: pass
    
    ram = "Desconocido"
    try:
        with open("/proc/meminfo") as f:
            for line in f:
                if "MemTotal" in line:
                    kb = int(line.split()[1])
                    ram = f"{kb/1024/1024:.1f} GB"
                    break
    except: pass
    
    table.add_row("[cyan]OS:[/cyan]", "CachyOS / Arch Linux")
    table.add_row("[cyan]CPU:[/cyan]", cpu[:25] + "..." if len(cpu)>25 else cpu)
    table.add_row("[cyan]RAM:[/cyan]", ram)
    table.add_row("[cyan]Tema Elegido:[/cyan]", f"[bold green]{user_choices['theme']}[/bold green]")
    table.add_row("[cyan]Drivers:[/cyan]", f"[bold purple]{'NVIDIA' if 'NVIDIA' in user_choices['drivers'] else 'Mesa (AMD/Intel)'}[/bold purple]")
    return table

# --- Layout Setup ---
layout = Layout()
layout.split_row(
    Layout(name="left", ratio=1),
    Layout(name="right", ratio=2)
)

layout["right"].split_column(
    Layout(name="progress", ratio=1),
    Layout(name="matrix", ratio=2)
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
    layout["left"]["logo"].update(Panel(Align.center(f"[bold cyan]{logo_text}[/bold cyan]"), border_style="cyan"))
    layout["left"]["sysinfo"].update(Panel(get_sys_info(), title="[bold blue]Hardware & Setup[/bold blue]", border_style="blue"))
    layout["right"]["progress"].update(Panel(progress, title="[bold green]Progreso de Metamorfosis[/bold green]", border_style="green"))
    
    matrix_text = "\n".join(log_lines)
    layout["right"]["matrix"].update(Panel(Text.from_markup(matrix_text, markup=False) if False else matrix_text, title="[bold yellow]The Matrix (Live Log)[/bold yellow]", border_style="yellow"))
    return layout

# --- Worker Thread ---
def installer_worker():
    global install_error, install_done
    try:
        # 1. Health Check
        progress.update(t_health, description="[yellow]Verificando Red...", advance=30)
        run_cmd_live("ping -c 1 archlinux.org")
        progress.update(t_health, description="[yellow]Verificando Espacio en Disco...", advance=30)
        free_space = shutil.disk_usage("/").free
        if free_space < 15 * 1024 * 1024 * 1024:
            raise Exception("Espacio insuficiente. Se requieren al menos 15GB libres en /.")
        progress.update(t_health, description="[green]Sistema en Óptimas Condiciones", completed=100)
        
        # 2. Repositorios
        progress.update(t_repo, description="[yellow]Desbloqueando Pacman...", advance=30)
        if os.path.exists("/var/lib/pacman/db.lck"):
            run_cmd_live("sudo rm -f /var/lib/pacman/db.lck")
        
        progress.update(t_repo, description="[yellow]Inyectando repo Omarchy...", advance=50)
        run_cmd_live("sudo bash -c 'grep -q \"omarchy\" /etc/pacman.conf || echo -e \"\\n[omarchy]\\nSigLevel = Optional TrustAll\\nServer = https://pkgs.omarchy.org/\\$arch/\\n\" >> /etc/pacman.conf'")
        progress.update(t_repo, description="[green]Repositorio Listo", completed=100)

        # 3. Sincronización
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

        # 4. Paquetes
        progress.update(t_pkg, description="[yellow]Calculando paquetes base...", advance=20)
        pkgs = []
        if os.path.exists("install/omarchy-base.packages"):
            with open("install/omarchy-base.packages") as f1:
                pkgs.extend(f1.read().splitlines())
        if os.path.exists("install/omarchy-other.packages"):
            with open("install/omarchy-other.packages") as f2:
                pkgs.extend(f2.read().splitlines())
        
        # Inyectar paquetes personalizados por el usuario
        pkgs.extend(user_choices["packages"])
        
        pkg_str = " ".join([p for p in pkgs if p and not p.startswith('#')])
        
        chk = subprocess.run(f"pacman -T {pkg_str}", shell=True, stdout=subprocess.PIPE, text=True)
        if chk.returncode != 0:
            missing = chk.stdout.replace('\n', ' ').strip()
            progress.update(t_pkg, description="[cyan]Descargando e Instalando...", advance=40)
            run_cmd_live("sudo pacman -Rdd --noconfirm jack2", check=False)
            run_cmd_live(f"sudo pacman -S --noconfirm {missing}")
        progress.update(t_pkg, description="[green]Paquetes Instalados", completed=100)

        # 5. Backup
        progress.update(t_backup, description="[yellow]Comprimiendo ~/.config...", advance=50)
        home = os.path.expanduser("~")
        backup_name = f"x64-backup-{datetime.now().strftime('%Y%m%d_%H%M%S')}.tar.gz"
        run_cmd_live(f"tar -czf {backup_name} -C {home} .config", check=False)
        progress.update(t_backup, description="[green]Respaldo Completado", completed=100)

        # 6. Configuraciones
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

# --- Launch Sequence ---
# 1. Interactive Setup
interactive_setup()

# 2. Main Dashboard Loop
with open(LOG_FILE, "w") as f:
    f.write("=== Inicio de Instalación X64-Omarchy (Mega Dashboard) ===\n")

start_time = time.time()
worker = threading.Thread(target=installer_worker)
worker.start()

with Live(update_ui(), refresh_per_second=10, screen=True) as live:
    while not install_done:
        time.sleep(0.1)
        live.update(update_ui())
        
    end_time = time.time()
    
    if install_error:
        layout["right"]["progress"].update(Panel(f"[bold red]ERROR CRÍTICO DURANTE LA INSTALACIÓN[/bold red]\n\n{install_error}\n\nRevisa el archivo {LOG_FILE}", border_style="red", title="Fallo del Sistema"))
    else:
        layout["right"]["progress"].update(Panel(Align.center("\n\n[bold green]¡Metamorfosis Completada con Éxito![/bold green]\n\n[bold cyan]Generando Reporte Final...[/bold cyan]\n"), title="Finalizado", border_style="green"))
    
    live.update(update_ui())
    time.sleep(3)

# 3. Final Report
print("\n")
if not install_error:
    time_taken = end_time - start_time
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
    console.print(Panel(f"[bold red]La instalación falló: {install_error}[/bold red]", expand=False))
