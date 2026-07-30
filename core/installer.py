import os
import shutil
import time
import subprocess
from datetime import datetime
import core.state as state
from core.engine import run_cmd_live
import core.ui as ui

def setup_plymouth_bootloader(has_nvidia_gpu=False):
    state.log_lines.append("[yellow]Aplicando tema de Plymouth...[/yellow]")
    run_cmd_live("sudo mkdir -p /usr/share/plymouth/themes/omarchy", check=False)
    run_cmd_live("sudo cp -r default/plymouth/* /usr/share/plymouth/themes/omarchy/ 2>/dev/null", check=False)
    run_cmd_live("sudo plymouth-set-default-theme omarchy", check=False)
    
    state.log_lines.append("[yellow]Configurando mkinitcpio (HOOKS & KMS)...[/yellow]")
    run_cmd_live("sudo bash -c 'grep -q \" plymouth\" /etc/mkinitcpio.conf || sed -i -E \"s/^(HOOKS=\\([^)]*\\b)(udev|systemd)(\\b)/\\1\\2 plymouth/\" /etc/mkinitcpio.conf' 2>/dev/null", check=False)
    
    if has_nvidia_gpu:
        state.log_lines.append("[yellow]Inyectando Early KMS para NVIDIA...[/yellow]")
        run_cmd_live("sudo bash -c 'grep -q \"nvidia_drm?\" /etc/mkinitcpio.conf || sed -i -E \"s/^MODULES=\\(([^)]*)\\)/MODULES=(\\1 nvidia? nvidia_modeset? nvidia_uvm? nvidia_drm?)/\" /etc/mkinitcpio.conf' 2>/dev/null", check=False)
        run_cmd_live("sudo bash -c 'sed -i \"s/nvidia nvidia/nvidia/g\" /etc/mkinitcpio.conf' 2>/dev/null", check=False)
    
    run_cmd_live("sudo sed -i '/COMPRESSION/d' /etc/mkinitcpio.conf", check=False)
    with open("/tmp/mkinitcpio_add.conf", "w") as f:
        f.write('COMPRESSION="zstd"\nCOMPRESSION_OPTIONS=("-T0")\n')
    run_cmd_live("sudo bash -c 'cat /tmp/mkinitcpio_add.conf >> /etc/mkinitcpio.conf'", check=False)
    
    state.log_lines.append("[yellow]Compilando módulos DKMS (Multihilo)...[/yellow]")
    run_cmd_live("sudo dkms autoinstall -j $(nproc)", check=False)
    
    run_cmd_live("echo '' | sudo mkinitcpio -P", check=False)
    
    state.log_lines.append("[yellow]Configurando Dracut (Fallback)...[/yellow]")
    run_cmd_live("sudo mkdir -p /etc/dracut.conf.d", check=False)
    run_cmd_live("sudo bash -c 'echo \"add_dracutmodules+=\\\" plymouth \\\"\" > /etc/dracut.conf.d/plymouth.conf'", check=False)
    if has_nvidia_gpu:
        run_cmd_live("sudo bash -c 'echo \"force_drivers+=\\\" nvidia nvidia_modeset nvidia_uvm nvidia_drm \\\"\" >> /etc/dracut.conf.d/plymouth.conf'", check=False)
    
    state.log_lines.append("[yellow]Buscando e inyectando configuración en Limine...[/yellow]")
    cmdline_extra = " splash"
    if has_nvidia_gpu:
        run_cmd_live("sudo mkdir -p /etc/modprobe.d", check=False)
        run_cmd_live("sudo bash -c 'echo \"options nvidia_drm modeset=1 fbdev=1\" > /etc/modprobe.d/nvidia-kms.conf'", check=False)
        
    run_cmd_live(f"sudo bash -c 'if [ -f /etc/kernel/cmdline ]; then grep -q \"splash\" /etc/kernel/cmdline || sed -i \"s/$/{cmdline_extra}/\" /etc/kernel/cmdline; fi' 2>/dev/null", check=False)
    
    limine_paths = ["/boot/limine.conf", "/boot/limine/limine.conf", "/efi/limine.conf", "/boot/efi/limine.conf",
                    "/boot/limine.cfg", "/boot/limine/limine.cfg", "/efi/limine.cfg", "/boot/efi/limine.cfg"]
    for lpath in limine_paths:
        if os.path.exists(lpath):
            run_cmd_live(f"sudo bash -c 'grep -q \"splash\" {lpath} || sudo sed -i -E \"/^ *kernel_cmdline/ {{ /splash/! s/$/{cmdline_extra}/ }}\" {lpath}' 2>/dev/null", check=False)
            run_cmd_live(f"sudo bash -c 'grep -q \"splash\" {lpath} || sudo sed -i -E \"/^ *cmdline/ {{ /splash/! s/$/{cmdline_extra}/ }}\" {lpath}' 2>/dev/null", check=False)
            break
    
    run_cmd_live("if command -v limine-update >/dev/null; then echo '' | sudo limine-update; fi", check=False)

def installer_worker():
    try:
        ui.progress.update(ui.t_health, description="[yellow]Verificando Red...", advance=30)
        run_cmd_live("ping -c 1 archlinux.org")
        ui.progress.update(ui.t_health, description="[yellow]Verificando Espacio en Disco...", advance=30)
        free_space = shutil.disk_usage("/").free
        if free_space < 15 * 1024 * 1024 * 1024:
            raise Exception("Espacio insuficiente. Se requieren al menos 15GB libres en /.")
        ui.progress.update(ui.t_health, description="[yellow]Ajustando flags de BTRFS en fstab (I/O Extremo)...", advance=15)
        run_cmd_live("sudo bash -c 'if [ -f /etc/fstab ]; then sed -i -E \"/btrfs/ s/(defaults|[a-z0-9=,]+)/\\1,noatime,space_cache=v2,discard=async/g\" /etc/fstab; fi'", check=False)
        run_cmd_live("sudo bash -c 'if [ -f /etc/fstab ]; then sed -i \"s/,,/,/g\" /etc/fstab; fi'", check=False)

        ui.progress.update(ui.t_health, description="[green]Sistema en Óptimas Condiciones", completed=100)
        
        ui.progress.update(ui.t_repo, description="[yellow]Acelerando Descargas (ParallelDownloads)...", advance=20)
        run_cmd_live("sudo sed -i 's/^#ParallelDownloads.*/ParallelDownloads = 10/' /etc/pacman.conf", check=False)
        run_cmd_live("sudo bash -c 'grep -q \"^ILoveCandy\" /etc/pacman.conf || sed -i \"/^#Color/a ILoveCandy\" /etc/pacman.conf'", check=False)
        run_cmd_live("sudo bash -c 'grep -q \"NoExtract = usr/share/doc\" /etc/pacman.conf || echo -e \"\\nNoExtract = usr/share/doc/* usr/share/gtk-doc/* usr/share/help/* usr/share/man/* usr/share/info/*\\n\" >> /etc/pacman.conf'", check=False)
        
        ui.progress.update(ui.t_repo, description="[yellow]Desbloqueando Pacman...", advance=10)
        if os.path.exists("/var/lib/pacman/db.lck"):
            run_cmd_live("sudo rm -f /var/lib/pacman/db.lck")
        
        ui.progress.update(ui.t_repo, description="[yellow]Inyectando repo Omarchy...", advance=50)
        run_cmd_live("sudo bash -c 'grep -q \"omarchy\" /etc/pacman.conf || echo -e \"\\n[omarchy]\\nSigLevel = Optional TrustAll\\nServer = https://pkgs.omarchy.org/\\$arch/\\n\" >> /etc/pacman.conf'")
        ui.progress.update(ui.t_repo, description="[yellow]Inyectando Chaotic-AUR...", advance=10)
        run_cmd_live("sudo pacman-key --recv-key 3056513887B78AEB --keyserver keyserver.ubuntu.com", check=False)
        run_cmd_live("sudo pacman-key --lsign-key 3056513887B78AEB", check=False)
        run_cmd_live("sudo pacman -U --noconfirm 'https://cdn-mirror.chaotic.cx/chaotic-aur/chaotic-keyring.pkg.tar.zst' 'https://cdn-mirror.chaotic.cx/chaotic-aur/chaotic-mirrorlist.pkg.tar.zst'", check=False)
        run_cmd_live("sudo bash -c 'grep -q \"chaotic-aur\" /etc/pacman.conf || echo -e \"\\n[chaotic-aur]\\nInclude = /etc/pacman.d/chaotic-mirrorlist\\n\" >> /etc/pacman.conf'")
        ui.progress.update(ui.t_repo, description="[green]Repositorios Listos", completed=100)


        ui.progress.update(ui.t_sync, description="[yellow]Creando Snapshot BTRFS...", advance=5)
        run_cmd_live("sudo snapper create -c root -d 'Pre-Omarchy Installation'", check=False)
        
        ui.progress.update(ui.t_sync, description="[yellow]Instalando Cabeceras del Kernel (Para DKMS)...", advance=5)
        run_cmd_live("sudo bash -c 'pacman -S --noconfirm --needed $(pacman -Qq | grep \"^linux\" | grep -v \"headers\" | grep -v \"firmware\" | awk \"{print \\$1\\\"-headers\\\"}\")' 2>/dev/null", check=False)

        ui.progress.update(ui.t_sync, description="[yellow]Sincronizando firmas (Puede tardar)...", advance=5)
        res = run_cmd_live("sudo eatmydata pacman -Syu --noconfirm", check=False)
        if res != 0:
            state.log_lines.append("[bold red]Fallo detectado. Reparando Llavero GPG...[/bold red]")
            run_cmd_live("sudo rm -rf /etc/pacman.d/gnupg/")
            ui.progress.update(ui.t_sync, description="[yellow]Reparando Llavero...", advance=10)
            run_cmd_live("sudo pacman-key --init")
            run_cmd_live("sudo pacman-key --populate archlinux cachyos")
            ui.progress.update(ui.t_sync, description="[yellow]Reintentando Sincronización...", advance=20)
            run_cmd_live("sudo eatmydata pacman -Syu --noconfirm")
        ui.progress.update(ui.t_sync, description="[green]Sistema Sincronizado", completed=100)

        ui.progress.update(ui.t_pkg, description="[yellow]Calculando paquetes base...", advance=20)
        pkgs = []
        if os.path.exists("install/omarchy-base.packages"):
            with open("install/omarchy-base.packages") as f1:
                pkgs.extend(f1.read().splitlines())
        if os.path.exists("install/omarchy-other.packages"):
            with open("install/omarchy-other.packages") as f2:
                pkgs.extend(f2.read().splitlines())
        
        pkgs.extend(["plymouth", "greetd", "greetd-tuigreet", "eatmydata"])
        pkgs.extend(state.user_choices["packages"])
        valid_pkgs = [p for p in pkgs if p and not p.startswith('#')]
        
        chk = subprocess.run(["pacman", "-T"] + valid_pkgs, stdout=subprocess.PIPE, text=True)
        if chk.returncode != 0:
            missing_pkgs = [p for p in chk.stdout.splitlines()]
            ui.progress.update(ui.t_pkg, description="[cyan]Descargando e Instalando Transacción Maestra...", advance=40)
            run_cmd_live("sudo pacman -Rdd --noconfirm jack2", check=False)
            run_cmd_live(f"sudo eatmydata pacman -S --noconfirm {' '.join(missing_pkgs)}")
        ui.progress.update(ui.t_pkg, description="[green]Paquetes Instalados", completed=100)

        ui.progress.update(ui.t_backup, description="[yellow]Comprimiendo ~/.config...", advance=50)
        home = os.path.expanduser("~")
        backup_name = f"x64-backup-{datetime.now().strftime('%Y%m%d_%H%M%S')}.tar.gz"
        run_cmd_live(f"tar -czf {backup_name} -C {home} .config", check=False)
        ui.progress.update(ui.t_backup, description="[green]Respaldo Completado", completed=100)

        ui.progress.update(ui.t_config, description="[yellow]Desplegando escudo de sistema...", advance=20)
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
        
        shutil.copytree("config", os.path.expanduser("~/.config"), dirs_exist_ok=True)
        
        if state.is_legacy_nvidia:
            autostart_path = os.path.expanduser("~/.config/hypr/autostart.lua")
            if os.path.exists(autostart_path):
                with open(autostart_path, "a") as f:
                    f.write('\no.launch_on_start("killall waybar swaybg")\n')
                    f.write('o.launch_on_start("quickshell -n -p /usr/share/omarchy/shell")\n')
                    
        shutil.copytree("bin", os.path.expanduser("~/.local/bin"), dirs_exist_ok=True)
        shutil.copytree("themes", os.path.expanduser("~/.local/share/themes"), dirs_exist_ok=True)
        run_cmd_live("chmod +x ~/.local/bin/*", check=False)
        
        ui.progress.update(ui.t_config, description="[yellow]Configurando Pantalla de Arranque (Plymouth)...", advance=5)
        setup_plymouth_bootloader(state.has_nvidia)
        
        ui.progress.update(ui.t_config, description="[yellow]Desplegando Gestor TUI (Tuigreet)...", advance=5)
        
        run_cmd_live("sudo mkdir -p /etc/greetd", check=False)
        
        run_cmd_live("sudo mkdir -p /etc/systemd/system/greetd.service.d", check=False)
        with open("/tmp/plymouth-fix.conf", "w") as f:
            f.write("[Service]\nExecStartPre=-/usr/bin/plymouth quit\n")
        run_cmd_live("sudo mv /tmp/plymouth-fix.conf /etc/systemd/system/greetd.service.d/plymouth-fix.conf", check=False)
        
        if state.is_legacy_nvidia:
            fish_autostart = """if status is-login
    if test (tty) = /dev/tty1
        exec Hyprland
    end
end
"""
            run_cmd_live("mkdir -p ~/.config/fish/conf.d", check=False)
            with open(os.path.expanduser("~/.config/fish/conf.d/hyprland_autostart.fish"), "w") as f:
                f.write(fish_autostart)
                
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
entrar automáticamente al entorno gráfico de Omarchy.\\e[0m

\\e[1;31m>>> MODO DE RESCATE (MANTENIMIENTO) <<<\\e[0m
\\e[1;37mSi necesitas reparar el sistema o instalar drivers sin gráfica, 
presiona \\e[1;33mCtrl + Alt + F2\\e[1;37m (o F3 a F6) para usar una consola pura.\\e[0m

\\e[38;2;0;255;150m> INGRESA TUS CREDENCIALES ABAJO:\\e[0m

"""
            with open("/tmp/issue.omarchy", "w", encoding="utf-8") as f:
                f.write(issue_omarchy)
            run_cmd_live("sudo mv /tmp/issue.omarchy /etc/issue.omarchy", check=False)
            
            run_cmd_live("sudo bash -c 'echo -e \"\\\\S \\\\r (\\\\l)\\\\n\" > /etc/issue'", check=False)
            run_cmd_live("sudo mkdir -p /etc/systemd/system/getty@tty1.service.d/", check=False)
            getty_override = """[Service]
ExecStart=
ExecStart=-/sbin/agetty -o '-p -- \\u' --noclear --issue-file /etc/issue.omarchy %I $TERM
"""
            with open("/tmp/issue.conf", "w") as f:
                f.write(getty_override)
            run_cmd_live("sudo mv /tmp/issue.conf /etc/systemd/system/getty@tty1.service.d/issue.conf", check=False)
            
        else:
            greetd_config = """[terminal]
vt = 1
[default_session]
command = "tuigreet --cmd 'uwsm start hyprland-uwsm.desktop' --asterisks --time --greeting 'Bienvenido a Omarchy Cyberpunk Environment' --remember --remember-user-session --sessions /usr/share/wayland-sessions"
user = "greeter"
"""
            with open("/tmp/greetd_config.toml", "w") as f:
                f.write(greetd_config)
            run_cmd_live("sudo mv /tmp/greetd_config.toml /etc/greetd/config.toml", check=False)

        ui.progress.update(ui.t_config, description="[yellow]Aplicando configuraciones finales (Batch Shell)...", advance=10)
        services_script = "#!/bin/bash\n"
        
        if not state.is_legacy_nvidia:
            services_script += "mkdir -p /usr/share/sddm/themes/omarchy /etc/sddm.conf.d\n"
            services_script += "cp -r default/sddm/omarchy/* /usr/share/sddm/themes/omarchy/ 2>/dev/null\n"
            services_script += "echo -e \"[Theme]\\nCurrent=omarchy\" > /etc/sddm.conf.d/omarchy.conf\n"
            services_script += "systemctl disable greetd.service 2>/dev/null\n"
            services_script += "systemctl enable sddm.service --now\n"
        else:
            services_script += "systemctl disable sddm.service 2>/dev/null\n"
            services_script += "systemctl disable greetd.service 2>/dev/null\n"
            services_script += "systemctl enable getty@tty1.service --now\n"

        services_script += "systemctl enable bluetooth.service\n"
        
        if "ananicy-cpp" in state.user_choices["packages"]:
            services_script += "systemctl enable ananicy-cpp.service\n"
        if "zram-generator" in state.user_choices["packages"]:
            services_script += "systemctl daemon-reload\n"
            services_script += "systemctl restart systemd-zram-setup@zram0.service\n"
        if "uksmd" in state.user_choices["packages"]:
            services_script += "systemctl enable uksmd.service\n"
        if "irqbalance" in state.user_choices["packages"]:
            services_script += "systemctl enable irqbalance.service\n"
        if "cups" in state.user_choices["packages"]:
            services_script += "systemctl enable cups.service\n"
            
        with open("/tmp/omarchy-services.sh", "w") as f:
            f.write(services_script)
        run_cmd_live("sudo bash /tmp/omarchy-services.sh", check=False)
        
        ui.progress.update(ui.t_config, description="[yellow]Aplicando Diseño y Tema...", advance=20)
        if state.user_choices["theme"] == "Tokyo Night":
            run_cmd_live("export OMARCHY_PATH=/usr/share/omarchy && export OMARCHY_THEME_HEADLESS=1 && /usr/share/omarchy/bin/omarchy-theme-set 'Tokyo Night'", check=False)
        
        ui.progress.update(ui.t_config, description="[yellow]Purgando caché de Pacman...", advance=10)
        run_cmd_live("sudo pacman -Scc --noconfirm", check=False)
        
        ui.progress.update(ui.t_config, description="[green]Sistema Listo", completed=100)
        
        if state.is_legacy_nvidia:
            run_cmd_live("echo -e '\\n\033[1;41m[ ALERTA NVIDIA LEGACY ]\033[0m\\nHardware antiguo detectado. El protocolo de rescate se ha inyectado. Por favor, inicia sesión escribiendo: \033[1;33mHyprland\033[0m (No uses UWSM ni el display manager).'", check=False)
            time.sleep(5)
            
    except Exception as e:
        state.install_error = str(e)
    finally:
        state.install_done = True
        state.current_state = "error" if state.install_error else "done"
