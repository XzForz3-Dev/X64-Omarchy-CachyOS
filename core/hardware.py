import subprocess
from rich.table import Table
import core.state as state

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
                lines = raw_text.split('\n')
                get_sys_info.ff_text = "\n".join(lines)
                get_sys_info.cached_rows = []
                for line in lines:
                    if line.strip() == "" or "---" in line:
                        continue
                    if ":" in line:
                        k, v = line.split(":", 1)
                        get_sys_info.cached_rows.append((f"[bold cyan]{k.strip()}[/bold cyan]", f"[white]{v.strip()}[/white]"))
                    else:
                        get_sys_info.cached_rows.append((f"[bold cyan]{line.strip()}[/bold cyan]", ""))
        except Exception:
            get_sys_info.ff_text = "Fastfetch no disponible"
            
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
