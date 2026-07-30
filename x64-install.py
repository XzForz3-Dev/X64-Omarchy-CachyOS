#!/usr/bin/env python3
# ==============================================================================
# X64-Omarchy-CachyOS Installer - Mega Dashboard (Python TUI Edition)
# By X64 Studios (MODULAR ARCHITECTURE)
# ==============================================================================

import os
import sys
import time
import threading

try:
    from rich.live import Live
    from rich.table import Table
    from rich.prompt import Prompt
    from rich.panel import Panel
except ImportError:
    print("Fatal: python-rich not found. Please run the installer via x64-install.sh")
    sys.exit(1)

if os.geteuid() == 0:
    print("Por favor NO ejecutes este script como root. Ejecútalo como tu usuario normal.")
    sys.exit(1)

# Import modular core
import core.state as state
import core.engine as engine
import core.hardware as hardware
import core.ui as ui
import core.installer as installer

# Iniciar la Sincronización Fantasma inmediatamente en background
threading.Thread(target=engine.precache_worker, daemon=True).start()
threading.Thread(target=engine.keep_sudo_alive, daemon=True).start()

# --- Launch Sequence ---
with open(state.LOG_FILE, "w") as f:
    f.write("=== Inicio de Instalación X64-Omarchy (Mega Dashboard Modular) ===\n")

hardware.detect_gpu_and_update_menu()

# Precargar fastfetch antes de iniciar la UI para evitar parpadeos de carga
hardware.get_sys_info()

try:
    with Live(ui.update_ui(), refresh_per_second=4) as live:
        k_worker = threading.Thread(target=ui.keyboard_worker, daemon=True)
        k_worker.start()
        
        while not state.install_done:
            time.sleep(0.25)
            
            if state.current_state == "error" and state.error_prompt:
                live.stop()
                os.system("clear")
                print(f"\n\033[1;41m[ ATENCIÓN - ERROR CRÍTICO ]\033[0m")
                print(f"\033[1;33m{state.error_prompt['msg']}\033[0m\n")
                ans = Prompt.ask("¿Cómo deseas proceder?", choices=["Reintentar", "Ignorar", "Abortar"], default="Reintentar")
                state.error_response = ans
                state.error_prompt = None
                os.system("clear")
                live.start()
            elif state.current_state == "working" and not state.start_time:
                state.start_time = time.time()
                worker = threading.Thread(target=installer.installer_worker, daemon=True)
                worker.start()
                
            live.update(ui.update_ui())
                
        state.end_time = time.time()
        live.update(ui.update_ui())
        time.sleep(2)
except KeyboardInterrupt:
    state.install_error = "Instalación abortada por el usuario (Ctrl+C)."
    state.install_done = True

print("\n")
if not state.install_error:
    time_taken = state.end_time - state.start_time if state.start_time else 0
    mins, secs = divmod(time_taken, 60)
    
    report = Table(title="[bold cyan]Reporte Final de Metamorfosis X64[/bold cyan]", box=None, expand=True)
    report.add_column("Métrica", style="cyan")
    report.add_column("Detalle", style="white")
    
    report.add_row("Tiempo de Instalación", f"{int(mins)}m {int(secs)}s")
    report.add_row("Tema Base", state.user_choices["theme"])
    report.add_row("Drivers Instalados", state.user_choices["drivers"])
    report.add_row("Software Extra Elegido", f"{len(state.user_choices['packages'])} paquetes")
    if len(state.user_choices["packages"]) > 0:
        report.add_row("Lista de Software", ", ".join(state.user_choices["packages"]))
    report.add_row("Archivo de Log", f"[dim]{state.LOG_FILE}[/dim]")
    
    state.console.print(Panel(report, border_style="green", title="[bold green]¡Sistema Listo![/bold green]"))
    
    ans = Prompt.ask("\n¿Deseas reiniciar el sistema ahora?", choices=["Si", "No"], default="Si")
    if ans == "Si":
        os.system("sudo reboot")
    else:
        print("\n[!] Puedes reiniciar más tarde ejecutando 'reboot'.\n")
else:
    state.console.print(Panel(f"[bold red]La instalación fue abortada: {state.install_error}[/bold red]", expand=False))

try:
    os.system(f"sudo cp {state.LOG_FILE} /var/log/x64-omarchy-install.log 2>/dev/null")
except Exception:
    pass
