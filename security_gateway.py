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

def get_term_size():
    try:
        res = subprocess.check_output(['stty', 'size'], stderr=subprocess.DEVNULL).decode().split()
        return int(res[0]), int(res[1])
    except:
        return 24, 80

def render_ui(password_len, msg=""):
    rows, cols = get_term_size()
    logo_lines = logo_text.strip('\n').split('\n')
    logo_height = len(logo_lines)
    logo_width = 83 
    
    pad_top = max(0, (rows - (logo_height + 8)) // 2)
    
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.write("\n" * pad_top)
    
    for line in logo_lines:
        pad_left = max(0, (cols - logo_width) // 2)
        sys.stdout.write(" " * pad_left + line + "\n")
        
    sys.stdout.write("\n\n")
    
    prompt = "Contraseña de Administrador: "
    stars = "*" * password_len
    
    box_width = 70
    pad_left_box = max(0, (cols - box_width) // 2)
    
    sys.stdout.write(" " * pad_left_box + f"\033[1;36m╭{'─'*(box_width-2)}╮\033[0m\n")
    sys.stdout.write(" " * pad_left_box + f"\033[1;36m│\033[0m" + " "*(box_width-2) + f"\033[1;36m│\033[0m\n")
    
    content = f"\033[1;37m{prompt}\033[1;31m{stars}\033[0m"
    content_len_visual = len(prompt) + len(stars)
    pad_content_left = (box_width - 2 - content_len_visual) // 2
    pad_content_right = box_width - 2 - content_len_visual - pad_content_left
    
    sys.stdout.write(" " * pad_left_box + f"\033[1;36m│\033[0m" + " "*pad_content_left + content + " "*pad_content_right + f"\033[1;36m│\033[0m\n")
    
    if msg:
        msg_clean = msg.replace('\033[1;33m', '').replace('\033[1;31m', '').replace('\033[1;32m', '').replace('\033[0m', '')
        pad_msg_left = (box_width - 2 - len(msg_clean)) // 2
        pad_msg_right = box_width - 2 - len(msg_clean) - pad_msg_left
        sys.stdout.write(" " * pad_left_box + f"\033[1;36m│\033[0m" + " "*pad_msg_left + msg + " "*pad_msg_right + f"\033[1;36m│\033[0m\n")
    else:
        sys.stdout.write(" " * pad_left_box + f"\033[1;36m│\033[0m" + " "*(box_width-2) + f"\033[1;36m│\033[0m\n")
        
    sys.stdout.write(" " * pad_left_box + f"\033[1;36m╰{'─'*(box_width-2)}╯\033[0m\n")
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
