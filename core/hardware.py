import subprocess
from rich.table import Table
import core.state as state

import psutil

import re
import time
from rich.text import Text

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
        except Exception:
            pass
            
        if not get_sys_info.ff_text:
            get_sys_info.ff_text = "Detección de Hardware fallida (Fastfetch no disponible)."
            
    table.add_row(Text.from_markup(get_sys_info.ff_text))
    table.add_row("")
    
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
            except Exception:
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
            except Exception:
                pass
                
        get_sys_info.cached_rows = rows
        
    for row in get_sys_info.cached_rows:
        table.add_row(row)
        
    return table

def detect_gpu_and_update_menu():
    try:
        chk = subprocess.run(["lspci"], stdout=subprocess.PIPE, text=True, check=False)
        output = chk.stdout.lower()
        has_nvidia = False
        for line in output.split('\n'):
            if ('vga' in line or '3d' in line) and 'nvidia' in line:
                has_nvidia = True
                break
        
        state.has_nvidia = has_nvidia
        
        if has_nvidia:
            try:
                pacman_q = subprocess.run(["pacman", "-Q"], stdout=subprocess.PIPE, text=True, check=False)
                installed_pkgs = pacman_q.stdout.lower()
                if "nvidia-470xx-dkms" in installed_pkgs or "nvidia-390xx-dkms" in installed_pkgs:
                    state.is_legacy_nvidia = True
            except Exception:
                pass
        
        for cat in state.menu_data:
            if "Drivers Gráficos" in cat["cat"]:
                for item in cat["items"]:
                    if "NVIDIA" in item["label"]:
                        item["selected"] = has_nvidia and not state.is_legacy_nvidia
                        if state.is_legacy_nvidia:
                            item["desc"] += " [bold yellow](Nota: Hardware antiguo. Se usará TTY Pura para evitar crasheos.)[/bold yellow]"
                    elif "Mesa" in item["label"]:
                        item["selected"] = not has_nvidia
    except Exception:
        pass
