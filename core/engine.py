import asyncio
import subprocess
from datetime import datetime
from rich.markup import escape
import core.state as state

def log(msg):
    time_str = datetime.now().strftime('%H:%M:%S')
    with open(state.LOG_FILE, "a") as f:
        f.write(f"[{time_str}] {msg}\n")
    state.log_lines.append(f"[bold blue][{time_str}][/bold blue] [bold cyan]{msg}[/bold cyan]")

def run_cmd_live(cmd, check=True):
    async def _run():
        while True:
            log(f"Ejecutando (async): {cmd}")
            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT
            )
            
            with open(state.LOG_FILE, "a", buffering=8192) as f:
                async for line_bytes in process.stdout:
                    line_clean = line_bytes.decode('utf-8', errors='replace').strip()
                    if line_clean:
                        f.write(line_clean + "\n")
                        if "error" in line_clean.lower() or "warning" in line_clean.lower() or len(line_clean) > 10:
                            safe_line = escape(line_clean)
                            state.log_lines.append(f"[dim white]{safe_line}[/dim white]")
                        
            await process.wait()
            
            if check and process.returncode != 0:
                log(f"FALLO: El comando devolvió código {process.returncode}")
                state.current_state = "error"
                state.error_prompt = {"msg": f"El comando falló con código {process.returncode}:\n{cmd}"}
                
                while state.error_response is None:
                    await asyncio.sleep(0.1)
                    
                resp = state.error_response
                state.error_response = None
                state.current_state = "working"
                
                if resp == "Reintentar":
                    log(f"Reintentando comando: {cmd}")
                    continue
                elif resp == "Ignorar":
                    log(f"Ignorando error y continuando: {cmd}")
                    return process.returncode
                else:
                    raise Exception(f"Abortado por el usuario tras fallo en: {cmd}")
                    
            return process.returncode
            
    return asyncio.run(_run())

def precache_worker():
    subprocess.run("sudo pacman -Sy --noconfirm --needed libeatmydata", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
