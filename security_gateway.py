#!/usr/bin/env python3
import sys
import tty
import termios
import select
import subprocess
import os
import time

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

def render_ui(password_len, msg=""):
    rows, cols = get_term_size()
    
    # Clear screen
    sys.stdout.write("\033[2J\033[H")
    
    # 1. Hacker Window Frame (Cyan)
    color = "\033[1;36m"
    draw_at(1, 1, color + "╔" + "═"*(cols-2) + "╗\033[0m")
    for r in range(2, rows):
        draw_at(r, 1, color + "║\033[0m")
        draw_at(r, cols, color + "║\033[0m")
    draw_at(rows, 1, color + "╚" + "═"*(cols-2) + "╝\033[0m")
    
    # 2. Window Title
    title = "[ X64 SECURE TERMINAL ]"
    draw_at(1, max(1, (cols - len(title)) // 2 + 1), f"\033[1;33m{title}\033[0m")
    
    # 3. Logo (Moved higher)
    logo_lines = logo_text.strip('\n').split('\n')
    logo_height = len(logo_lines)
    logo_width = 83 
    
    start_y = 5 # Positioned higher up
    for i, line in enumerate(logo_lines):
        x = max(2, (cols - logo_width) // 2 + 1)
        draw_at(start_y + i, x, line)
        
    # 4. Password Box (Centered below logo)
    box_width = 70
    box_y = start_y + logo_height + 4
    box_x = max(2, (cols - box_width) // 2 + 1)
    
    draw_at(box_y, box_x, f"\033[1;36m╭{'─'*(box_width-2)}╮\033[0m")
    draw_at(box_y+1, box_x, f"\033[1;36m│\033[0m" + " "*(box_width-2) + f"\033[1;36m│\033[0m")
    draw_at(box_y+2, box_x, f"\033[1;36m╰{'─'*(box_width-2)}╯\033[0m")
    
    prompt = "Contraseña de Administrador: "
    stars = "*" * password_len
    content = f"\033[1;37m{prompt}\033[1;31m{stars}\033[0m"
    content_len_visual = len(prompt) + len(stars)
    pad_left = (box_width - 2 - content_len_visual) // 2
    
    draw_at(box_y+1, box_x + 1 + pad_left, content)
    
    # 5. Message Text
    if msg:
        msg_clean = msg.replace('\033[1;33m', '').replace('\033[1;31m', '').replace('\033[1;32m', '').replace('\033[0m', '')
        pad_msg = max(2, (cols - len(msg_clean)) // 2 + 1)
        draw_at(box_y+4, pad_msg, msg)
        
    # 6. Hacker Footer (OMARCHY + CACHYOS)
    footer_text = " [ OMARCHY + CACHYOS // CORE SYSTEM OVERRIDE ] "
    draw_at(rows - 2, max(2, (cols - len(footer_text)) // 2 + 1), f"\033[1;35m{footer_text}\033[0m")
    
    sys.stdout.flush()

def main():
    password = ""
    msg = ""
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    
    sys.stdout.write("\033[?25l") # Hide cursor
    try:
        tty.setcbreak(fd)
        
        while True:
            render_ui(len(password), msg)
            msg = ""
            
            while True:
                if select.select([sys.stdin], [], [], 0.05)[0]:
                    ch = sys.stdin.read(1)
                    
                    if ch == '\n' or ch == '\r':
                        if not password:
                            break
                        
                        render_ui(len(password), "\033[1;33mValidando credenciales en The Matrix...\033[0m")
                        
                        proc = subprocess.Popen(
                            ['sudo', '-S', '-v'],
                            stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE
                        )
                        out, err = proc.communicate(input=(password + '\n').encode())
                        
                        if proc.returncode == 0:
                            render_ui(len(password), "\033[1;32mAcceso Concedido. Desbloqueando...\033[0m")
                            time.sleep(1)
                            sys.stdout.write("\033[2J\033[H\033[?25h") # Show cursor, clear
                            sys.exit(0)
                        else:
                            password = ""
                            msg = "\033[1;31mAcceso Denegado. Contraseña incorrecta.\033[0m"
                            break
                            
                    elif ch == '\x7f' or ch == '\b': 
                        if len(password) > 0:
                            password = password[:-1]
                            break
                    elif ch == '\x03': 
                        sys.stdout.write("\033[?25h")
                        sys.exit(1)
                    else:
                        password += ch
                        break
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        sys.stdout.write("\033[?25h")

if __name__ == "__main__":
    main()
