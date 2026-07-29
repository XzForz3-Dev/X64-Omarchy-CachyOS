#!/usr/bin/env python3
# ==============================================================================
# X64-Omarchy-CachyOS Installer (TUI Python Edition)
# By X64 Studios
# ==============================================================================

import os
import sys
import subprocess
import time
from datetime import datetime

# Import rich elements
try:
    from rich.live import Live
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
    from rich.layout import Layout
    from rich.align import Align
    from rich.console import Console
except ImportError:
    print("Fatal: python-rich not found. Please run the installer via x64-install.sh")
    sys.exit(1)

if os.geteuid() == 0:
    print("Por favor NO ejecutes este script como root. Ejecútalo como tu usuario normal.")
    sys.exit(1)

LOG_FILE = "x64-install.log"
console = Console()

def log(msg):
    with open(LOG_FILE, "a") as f:
        f.write(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}\n")

def run_cmd(cmd, check=True):
    log(f"Ejecutando: {cmd}")
    result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    with open(LOG_FILE, "a") as f:
        f.write(result.stdout)
    if check and result.returncode != 0:
        log(f"ERROR Fatal: El comando falló con código {result.returncode}")
        raise Exception(f"Comando fallido (revisa el log): {cmd}")
    return result

progress = Progress(
    SpinnerColumn(),
    TextColumn("[progress.description]{task.description}"),
    BarColumn(),
    TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
)

layout = Layout()
layout.split_column(
    Layout(name="header", size=10),
    Layout(name="main")
)

logo = """
██╗  ██╗ ██████╗ ██╗  ██╗    ███████╗████████╗██╗   ██╗██████╗ ██╗ ██████╗ ███████╗
╚██╗██╔╝██╔════╝ ██║  ██║    ██╔════╝╚══██╔══╝██║   ██║██╔══██╗██║██╔═══██╗██╔════╝
 ╚███╔╝ ███████╗ ███████║    ███████╗   ██║   ██║   ██║██║  ██║██║██║   ██║███████╗
 ██╔██╗ ██╔═══██╗╚════██║    ╚════██║   ██║   ██║   ██║██║  ██║██║██║   ██║╚════██║
██╔╝ ██╗╚██████╔╝     ██║    ███████║   ██║   ╚██████╔╝██████╔╝██║╚██████╔╝███████║
╚═╝  ╚═╝ ╚═════╝      ╚═╝    ╚══════╝   ╚═╝    ╚═════╝ ╚═════╝ ╚═╝ ╚═════╝ ╚══════╝
"""
layout["header"].update(Panel(Align.center(f"[bold cyan]{logo}[/bold cyan]"), border_style="cyan"))
layout["main"].update(Panel(progress, title="Estado de Instalación", border_style="blue"))

t_net = progress.add_task("[white]Verificando Red...", total=100)
t_repo = progress.add_task("[white]Preparando Repositorios...", total=100)
t_sync = progress.add_task("[white]Sincronizando Sistema...", total=100)
t_pkg = progress.add_task("[white]Instalando X64-Omarchy...", total=100)
t_backup = progress.add_task("[white]Creando Respaldo...", total=100)
t_config = progress.add_task("[white]Aplicando Configuración...", total=100)

def execute_installation():
    try:
        # 1. Red
        progress.update(t_net, description="[yellow]Haciendo ping a servidores de Arch...", advance=20)
        run_cmd("ping -c 1 archlinux.org")
        progress.update(t_net, description="[green]Red Verificada", completed=100)
        
        # 2. Repositorios y Bloqueos
        progress.update(t_repo, description="[yellow]Desbloqueando Pacman si es necesario...", advance=30)
        if os.path.exists("/var/lib/pacman/db.lck"):
            run_cmd("sudo rm -f /var/lib/pacman/db.lck")
        
        progress.update(t_repo, description="[yellow]Inyectando repositorio Omarchy...", advance=50)
        pacman_conf = ""
        with open("/etc/pacman.conf", "r") as f:
            pacman_conf = f.read()
        
        if "[omarchy]" not in pacman_conf:
            run_cmd("sudo bash -c 'echo -e \"\\n[omarchy]\\nSigLevel = Optional TrustAll\\nServer = https://pkgs.omarchy.org/\\$arch/\\n\" >> /etc/pacman.conf'")
        progress.update(t_repo, description="[green]Repositorio Listo", completed=100)

        # 3. Sincronización
        progress.update(t_sync, description="[yellow]Sincronizando paquetes y firmas (puede tardar)...", advance=20)
        res = run_cmd("sudo pacman -Syu --noconfirm", check=False)
        if res.returncode != 0:
            progress.update(t_sync, description="[red]Error detectado. Reparando Llavero GPG...", advance=20)
            run_cmd("sudo rm -rf /etc/pacman.d/gnupg/")
            progress.update(t_sync, description="[yellow]Inicializando llaves...", advance=10)
            run_cmd("sudo pacman-key --init")
            progress.update(t_sync, description="[yellow]Poblando llaves de CachyOS...", advance=20)
            run_cmd("sudo pacman-key --populate archlinux cachyos")
            progress.update(t_sync, description="[yellow]Reintentando Sincronización...", advance=20)
            run_cmd("sudo pacman -Syu --noconfirm")
        progress.update(t_sync, description="[green]Sistema Sincronizado", completed=100)

        # 4. Paquetes
        progress.update(t_pkg, description="[yellow]Recopilando paquetes de X64-Omarchy...", advance=20)
        if not os.path.exists("install/omarchy-base.packages"):
            raise Exception("No se encontraron las listas de paquetes (omarchy-base.packages).")
        
        with open("install/omarchy-base.packages") as f1, open("install/omarchy-other.packages") as f2:
            pkgs = f1.read().splitlines() + f2.read().splitlines()
        
        valid_pkgs = [p for p in pkgs if p and not p.startswith('#')]
        pkg_str = " ".join(valid_pkgs)
        
        progress.update(t_pkg, description="[yellow]Filtrando paquetes instalados...", advance=20)
        chk = run_cmd(f"pacman -T {pkg_str}", check=False)
        if chk.returncode != 0:
            missing = chk.stdout.replace('\n', ' ').strip()
            progress.update(t_pkg, description="[cyan]Descargando núcleo e instalando componentes (Tomará tiempo)...", advance=40)
            run_cmd("sudo pacman -Rdd --noconfirm jack2", check=False)
            run_cmd(f"sudo pacman -S --noconfirm {missing}")
        progress.update(t_pkg, description="[green]Paquetes instalados", completed=100)

        # 5. Backup
        progress.update(t_backup, description="[yellow]Comprimiendo configuraciones actuales (~/.config)...", advance=50)
        home = os.path.expanduser("~")
        config_dir = os.path.join(home, ".config")
        backup_name = f"x64-backup-{datetime.now().strftime('%Y%m%d_%H%M%S')}.tar.gz"
        if os.path.exists(config_dir):
            run_cmd(f"tar -czf {backup_name} -C {home} .config", check=False)
        progress.update(t_backup, description="[green]Respaldo Completado", completed=100)

        # 6. Configuraciones Finales
        progress.update(t_config, description="[yellow]Desplegando archivos del sistema...", advance=20)
        run_cmd("mkdir -p ~/.config ~/.local/bin ~/.local/share/themes")
        run_cmd("sudo mkdir -p /usr/share/omarchy")
        run_cmd("sudo cp -r bin config default shell themes /usr/share/omarchy/", check=False)
        run_cmd("sudo chmod -R 755 /usr/share/omarchy")
        
        progress.update(t_config, description="[yellow]Configurando Sesión Wayland y SDDM...", advance=30)
        run_cmd("sudo mkdir -p /usr/share/wayland-sessions")
        run_cmd("sudo cp default/wayland-sessions/omarchy.desktop /usr/share/wayland-sessions/", check=False)
        run_cmd("sudo mkdir -p /usr/share/xdg-terminal-exec")
        run_cmd("sudo cp default/xdg-terminal-exec/hyprland-xdg-terminals.list /usr/share/xdg-terminal-exec/", check=False)
        
        run_cmd("sudo bash -c 'echo \"export OMARCHY_PATH=/usr/share/omarchy\" > /etc/profile.d/omarchy.sh'")
        run_cmd("sudo chmod +x /etc/profile.d/omarchy.sh")
        
        run_cmd("cp -r config/* ~/.config/", check=False)
        run_cmd("cp -r bin/* ~/.local/bin/", check=False)
        run_cmd("cp -r themes/* ~/.local/share/themes/", check=False)
        run_cmd("chmod +x ~/.local/bin/*", check=False)
        
        progress.update(t_config, description="[yellow]Habilitando servicios...", advance=20)
        run_cmd("sudo systemctl enable sddm.service --now", check=False)
        run_cmd("sudo systemctl enable bluetooth.service", check=False)
        
        progress.update(t_config, description="[yellow]Inicializando Tema...", advance=20)
        run_cmd("export OMARCHY_PATH=/usr/share/omarchy && /usr/share/omarchy/bin/omarchy-theme-set 'Tokyo Night'", check=False)
        
        progress.update(t_config, description="[green]Sistema Listo", completed=100)
        return True
    except Exception as e:
        log(f"EXCEPCION: {str(e)}")
        layout["main"].update(Panel(f"[bold red]ERROR CRÍTICO DURANTE LA INSTALACIÓN[/bold red]\n\n{str(e)}\n\nRevisa el archivo {LOG_FILE} para más detalles.", border_style="red", title="Fallo del Sistema"))
        return False

with open(LOG_FILE, "w") as f:
    f.write("=== Inicio de Instalación X64-Omarchy (TUI) ===\n")

success = False
with Live(layout, refresh_per_second=10, screen=True):
    success = execute_installation()
    if success:
        layout["main"].update(Panel(Align.center("\n\n[bold green]¡Metamorfosis Completada con Éxito![/bold green]\n\nTodos los paquetes, temas y scripts se han instalado y configurado correctamente.\nRevisa el archivo de log para ver los detalles técnicos.\n\n[bold cyan]El sistema está listo para ser reiniciado.[/bold cyan]\n"), title="Finalizado", border_style="green"))
    time.sleep(5)

print("\n")
if success:
    console.print(Panel("[bold green]¡Instalación Exitosa! Puedes reiniciar tu sistema ahora.[/bold green]", expand=False))
else:
    console.print(Panel("[bold red]La instalación falló. Revisa x64-install.log[/bold red]", expand=False))
