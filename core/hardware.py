import subprocess
from rich.table import Table
import core.state as state

import psutil

def get_sys_info():
    table = Table(show_header=False, expand=True, box=None)
    
    cpu_percent = psutil.cpu_percent()
    cpu_bar_len = int(cpu_percent / 5)
    cpu_bar = "█" * cpu_bar_len + "░" * (20 - cpu_bar_len)
    
    ram = psutil.virtual_memory()
    ram_percent = ram.percent
    ram_bar_len = int(ram_percent / 5)
    ram_bar = "█" * ram_bar_len + "░" * (20 - ram_bar_len)
    
    table.add_row(f"[bold cyan]CPU Usage[/bold cyan]", f"[yellow]{cpu_percent:>5.1f}%[/yellow] [green]{cpu_bar}[/green]")
    table.add_row(f"[bold cyan]RAM Usage[/bold cyan]", f"[yellow]{ram_percent:>5.1f}%[/yellow] [magenta]{ram_bar}[/magenta]")
    table.add_row("", "")
    
    if not hasattr(get_sys_info, "cached_rows"):
        get_sys_info.cached_rows = []
        try:
            res = subprocess.run(["fastfetch", "--logo", "none", "--structure", "OS:Host:Kernel:Packages:Display:WM:GPU:Disk"], stdout=subprocess.PIPE, text=True)
            if res.returncode == 0:
                for line in res.stdout.strip().split('\n'):
                    if line.strip() and ":" in line:
                        k, v = line.split(":", 1)
                        get_sys_info.cached_rows.append((f"[bold cyan]{k.strip()}[/bold cyan]", f"[white]{v.strip()}[/white]"))
        except Exception:
            pass
            
    for k, v in get_sys_info.cached_rows:
        table.add_row(k, v)
        
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
                        item["selected"] = has_nvidia
                        if state.is_legacy_nvidia:
                            item["desc"] += " [bold yellow](Nota: Hardware antiguo. Se usará TTY Pura para evitar crasheos.)[/bold yellow]"
                    elif "Mesa" in item["label"]:
                        item["selected"] = not has_nvidia
    except Exception:
        pass
