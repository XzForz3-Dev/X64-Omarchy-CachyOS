#!/usr/bin/env python3
import sys
import tty
import termios
import select
import subprocess
import os
import time
import random

logo_text = """
\033[1;36m██╗  ██╗ ██████╗ ██╗  ██╗    ███████╗████████╗██╗   ██╗██████╗ ██╗ ██████╗ ███████╗
╚██╗██╔╝██╔════╝ ██║  ██║    ██╔════╝╚══██╔══╝██║   ██║██╔══██╗██║██╔═══██╗██╔════╝
 ╚███╔╝ ███████╗ ███████║    ███████╗   ██║   ██║   ██║██║  ██║██║██║   ██║███████╗
 ██╔██╗ ██╔═══██╗╚════██║    ╚════██║   ██║   ██║   ██║██║  ██║██║██║   ██║╚════██║
██╔╝ ██╗╚██████╔╝     ██║    ███████║   ██║   ╚██████╔╝██████╔╝██║╚██████╔╝███████║
╚═╝  ╚═╝ ╚═════╝      ╚═╝    ╚══════╝   ╚═╝    ╚═════╝ ╚═════╝ ╚═╝ ╚═════╝ ╚══════╝\033[0m
"""

def draw_at(y, x, text):
    sys.stdout.write(f"\033[{y};{x}H{text}")

def get_term_size():
    try:
        res = subprocess.check_output(['stty', 'size'], stderr=subprocess.DEVNULL).decode().split()
        return int(res[0]), int(res[1])
    except:
        return 24, 80

def draw_static_ui():
    rows, cols = get_term_size()
    sys.stdout.write("\033[2J\033[H")
    
    color = "\033[1;36m"
    draw_at(1, 1, color + "╔" + "═"*(cols-2) + "╗\033[0m")
    sys.stdout.flush()
    time.sleep(0.02)
    
    for r in range(2, rows):
        draw_at(r, 1, color + "║\033[0m")
        draw_at(r, cols, color + "║\033[0m")
        sys.stdout.flush()
        time.sleep(0.005)
        
    draw_at(rows, 1, color + "╚" + "═"*(cols-2) + "╝\033[0m")
    sys.stdout.flush()
    
    title = "[ X64 SECURE TERMINAL ]"
    draw_at(1, max(1, (cols - len(title)) // 2 + 1), f"\033[1;33m{title}\033[0m")
    
    logo_lines = logo_text.strip('\n').split('\n')
    logo_width = 83 
    start_y = 5 
    
    for i, line in enumerate(logo_lines):
        x = max(2, (cols - logo_width) // 2 + 1)
        draw_at(start_y + i, x, line)
        sys.stdout.flush()
        time.sleep(0.04)
        
    text_y = start_y + len(logo_lines) + 2
    welcome_text = [
        "\033[1;36m✦ BIENVENIDO A LA COMUNIDAD X64 STUDIOS ✦\033[0m",
        "",
        "\033[1;37mSomos una comunidad apasionada de desarrolladores creando software,\033[0m",
        "\033[1;37mwebs, plugins y herramientas de última generación.\033[0m",
        "",
        "\033[1;90mEste instalador ha sido diseñado por X64 Studios para brindarte\033[0m",
        "\033[1;90mla experiencia definitiva al configurar Omarchy sobre CachyOS.\033[0m",
        "",
        "\033[1;33m\"Potenciando ideas, desarrollando el futuro.\"\033[0m"
    ]
    
    if rows >= 30:
        for i, text_line in enumerate(welcome_text):
            clean_line = text_line.replace('\033[1;36m', '').replace('\033[1;37m', '').replace('\033[1;90m', '').replace('\033[1;33m', '').replace('\033[0m', '')
            x = max(2, (cols - len(clean_line)) // 2 + 1)
            draw_at(text_y + i, x, text_line)
            sys.stdout.flush()
            time.sleep(0.02)
        box_y = text_y + len(welcome_text) + 2
    else:
        box_y = start_y + len(logo_lines) + 4
        
    box_width = 70
    box_x = max(2, (cols - box_width) // 2 + 1)
    
    draw_at(box_y, box_x, f"\033[1;36m╭{'─'*(box_width-2)}╮\033[0m")
    draw_at(box_y+1, box_x, f"\033[1;36m│\033[0m" + " "*(box_width-2) + f"\033[1;36m│\033[0m")
    draw_at(box_y+2, box_x, f"\033[1;36m╰{'─'*(box_width-2)}╯\033[0m")
    
    footer_text = " [ OMARCHY + CACHYOS // CORE SYSTEM OVERRIDE ] "
    draw_at(rows - 2, max(2, (cols - len(footer_text)) // 2 + 1), f"\033[1;35m{footer_text}\033[0m")
    
    sys.stdout.flush()

def update_dynamic_ui(password_len, msg="", scramble_char=None):
    rows, cols = get_term_size()
    logo_height = 6
    start_y = 5
    
    if rows >= 30:
        text_y = start_y + logo_height + 2
        box_y = text_y + 9 + 2
    else:
        box_y = start_y + logo_height + 4
        
    box_width = 70
    box_x = max(2, (cols - box_width) // 2 + 1)
    
    prompt = "Contraseña de Administrador: "
    
    if scramble_char and password_len > 0:
        stars = "*" * (password_len - 1) + f"\033[1;33m{scramble_char}\033[1;31m"
    else:
        stars = "*" * password_len
        
    content = f"\033[1;37m{prompt}\033[1;31m{stars}\033[0m"
    content_len_visual = len(prompt) + password_len
    pad_left = (box_width - 2 - content_len_visual) // 2
    
    # Overwrite the entire inner line to clear old characters
    blank_inner = " " * (box_width - 2)
    draw_at(box_y+1, box_x + 1, blank_inner)
    draw_at(box_y+1, box_x + 1 + pad_left, content)
    
    # Message line
    blank_msg = " " * (cols - 2)
    draw_at(box_y+4, 2, blank_msg)
    if msg:
        msg_clean = msg.replace('\033[1;33m', '').replace('\033[1;31m', '').replace('\033[1;32m', '').replace('\033[0m', '')
        pad_msg = max(2, (cols - len(msg_clean)) // 2 + 1)
        draw_at(box_y+4, pad_msg, msg)
        
    sys.stdout.flush()

def main():
    password = ""
    msg = ""
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    
    sys.stdout.write("\033[?25l") # Hide cursor
    try:
        draw_static_ui()
        update_dynamic_ui(0)
        
        tty.setcbreak(fd)
        
        while True:
            while True:
                if select.select([sys.stdin], [], [], 0.05)[0]:
                    ch = sys.stdin.read(1)
                    
                    if ch == '\n' or ch == '\r':
                        if not password:
                            break
                        
                        update_dynamic_ui(len(password), "\033[1;33mValidando credenciales en The Matrix...\033[0m")
                        
                        proc = subprocess.Popen(
                            ['sudo', '-S', '-v'],
                            stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE
                        )
                        out, err = proc.communicate(input=(password + '\n').encode())
                        
                        if proc.returncode == 0:
                            update_dynamic_ui(len(password), "\033[1;32mAcceso Concedido. Desbloqueando...\033[0m")
                            time.sleep(1)
                            sys.stdout.write("\033[2J\033[H\033[?25h") 
                            sys.exit(0)
                        else:
                            password = ""
                            msg = "\033[1;31mAcceso Denegado. Contraseña incorrecta.\033[0m"
                            update_dynamic_ui(len(password), msg)
                            break
                            
                    elif ch == '\x7f' or ch == '\b': 
                        if len(password) > 0:
                            password = password[:-1]
                            update_dynamic_ui(len(password), "")
                            break
                    elif ch == '\x03': 
                        sys.stdout.write("\033[?25h")
                        sys.exit(1)
                    else:
                        password += ch
                        
                        # Encryption effect
                        scramble_chars = "!@#$%^&*?/~X"
                        for _ in range(3):
                            update_dynamic_ui(len(password), "", scramble_char=random.choice(scramble_chars))
                            time.sleep(0.02)
                        update_dynamic_ui(len(password), "")
                        
                        break
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        sys.stdout.write("\033[?25h")

if __name__ == "__main__":
    main()
