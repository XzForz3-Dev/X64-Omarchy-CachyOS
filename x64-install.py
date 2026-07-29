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

def log(msg):
    time_str = datetime.now().strftime('%H:%M:%S')
    with open(LOG_FILE, "a") as f:
        f.write(f"[{time_str}] {msg}\n")
    log_lines.append(f"[bold blue][{time_str}][/bold blue] [bold cyan]{msg}[/bold cyan]")

def run_cmd_live(cmd, check=True):
    """Ejecuta un comando, captura la salida línea por línea y la muestra en la Matrix."""
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
    table.add_row("[cyan]Perfil:[/cyan]", "[bold green]X64-Omarchy Pro[/bold green]")
    table.add_row("[cyan]Modo:[/cyan]", "[bold purple]Dashboard TUI[/bold purple]")
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
"""

progress = Progress(
    SpinnerColumn(),
    TextColumn("[progress.description]{task.description}"),
    BarColumn(),
    TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
)
t_net = progress.add_task("[white]Verificando Red...", total=100)
t_repo = progress.add_task("[white]Preparando Repositorios...", total=100)
t_sync = progress.add_task("[white]Sincronizando Sistema...", total=100)
t_pkg = progress.add_task("[white]Instalando X64-Omarchy...", total=100)
t_backup = progress.add_task("[white]Creando Respaldo...", total=100)
t_config = progress.add_task("[white]Aplicando Configuración...", total=100)

def update_ui():
    """Genera la interfaz gráfica actualizada."""
    layout["left"]["logo"].update(Panel(Align.center(f"[bold cyan]{logo_text}[/bold cyan]\n[bold purple]STUDIOS[/bold purple]"), border_style="cyan"))
    layout["left"]["sysinfo"].update(Panel(get_sys_info(), title="[bold blue]Hardware Scanner[/bold blue]", border_style="blue"))
    layout["right"]["progress"].update(Panel(progress, title="[bold green]Progreso de Metamorfosis[/bold green]", border_style="green"))
    
    matrix_text = "\n".join(log_lines)
    layout["right"]["matrix"].update(Panel(matrix_text, title="[bold yellow]The Matrix (Live Log)[/bold yellow]", border_style="yellow"))
    return layout

# --- Worker Thread ---
def installer_worker():
    global install_error, install_done
    try:
        # 1. Red
        progress.update(t_net, description="[yellow]Haciendo ping a servidores...", advance=20)
        run_cmd_live("ping -c 1 archlinux.org")
        progress.update(t_net, description="[green]Red Verificada", completed=100)
        
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
        progress.update(t_pkg, description="[yellow]Calculando paquetes a descargar...", advance=20)
        with open("install/omarchy-base.packages") as f1, open("install/omarchy-other.packages") as f2:
            pkgs = f1.read().splitlines() + f2.read().splitlines()
        
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
        
        progress.update(t_config, description="[yellow]Cargando Tema Tokyo Night...", advance=20)
        run_cmd_live("export OMARCHY_PATH=/usr/share/omarchy && /usr/share/omarchy/bin/omarchy-theme-set 'Tokyo Night'", check=False)
        
        progress.update(t_config, description="[green]Sistema Listo", completed=100)
    except Exception as e:
        install_error = str(e)
    finally:
        install_done = True

# --- Main Loop ---
with open(LOG_FILE, "w") as f:
    f.write("=== Inicio de Instalación X64-Omarchy (Mega Dashboard) ===\n")

# Iniciar el hilo de trabajo (Worker Thread) para que la UI no se congele
worker = threading.Thread(target=installer_worker)
worker.start()

# Loop principal de la Interfaz Gráfica
with Live(update_ui(), refresh_per_second=10, screen=True) as live:
    while not install_done:
        time.sleep(0.1)
        live.update(update_ui())
        
    if install_error:
        layout["right"]["progress"].update(Panel(f"[bold red]ERROR CRÍTICO DURANTE LA INSTALACIÓN[/bold red]\n\n{install_error}\n\nRevisa el archivo {LOG_FILE}", border_style="red", title="Fallo del Sistema"))
    else:
        layout["right"]["progress"].update(Panel(Align.center("\n\n[bold green]¡Metamorfosis Completada con Éxito![/bold green]\n\n[bold cyan]El sistema está listo para ser reiniciado.[/bold cyan]\n"), title="Finalizado", border_style="green"))
    
    live.update(update_ui())
    time.sleep(5)

print("\n")
if not install_error:
    console.print(Panel("[bold green]¡Instalación Exitosa! Puedes reiniciar tu sistema ahora.[/bold green]", expand=False))
else:
    console.print(Panel(f"[bold red]La instalación falló: {install_error}[/bold red]", expand=False))
