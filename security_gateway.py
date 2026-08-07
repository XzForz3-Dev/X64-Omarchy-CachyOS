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
\033[1;32m██╗  ██╗ ██████╗ ██╗  ██╗    ███████╗████████╗██╗   ██╗██████╗ ██╗ ██████╗ ███████╗
╚██╗██╔╝██╔════╝ ██║  ██║    ██╔════╝╚══██╔══╝██║   ██║██╔══██╗██║██╔═══██╗██╔════╝
 ╚███╔╝ ███████╗ ███████║    ███████╗   ██║   ██║   ██║██║  ██║██║██║   ██║███████╗
 ██╔██╗ ██╔═══██╗╚════██║    ╚════██║   ██║   ██║   ██║██║  ██║██║██║   ██║╚════██║
██╔╝ ██╗╚██████╔╝     ██║    ███████║   ██║   ╚██████╔╝██████╔╝██║╚██████╔╝███████║
╚═╝  ╚═╝ ╚═════╝      ╚═╝    ╚══════╝   ╚═╝    ╚═════╝ ╚═════╝ ╚═╝ ╚═════╝ ╚══════╝\033[0m
"""

welcome_text = [
    "\033[1;36m✦ BIENVENIDO A LA COMUNIDAD X64 STUDIOS ✦\033[0m",
    "",
    "\033[1;37mSomos un colectivo élite de desarrolladores, ingenieros y diseñadores dedicados\033[0m",
    "\033[1;37ma superar los límites del software, desarrollo web y herramientas de última generación.\033[0m",
    "",
    "\033[1;37mNuestra filosofía es inquebrantable: construir ecosistemas digitales donde el rendimiento\033[0m",
    "\033[1;37mabsoluto converja perfectamente con una estética minimalista y superior.\033[0m",
    "",
    "\033[1;90mEste instalador exclusivo ha sido forjado desde cero por X64 Studios para brindarte\033[0m",
    "\033[1;90muna metamorfosis impecable de tu sistema, fusionando el poder de Omarchy y CachyOS.\033[0m",
    "",
    "\033[1;36m[ Únete a nuestras filas en Discord para colaborar, aprender y crear con nosotros ]\033[0m",
    "\033[1;36m\"Potenciando ideas, desarrollando el futuro.\"\033[0m"
]

def draw_at(y, x, text):
    sys.stdout.write(f"\033[{y};{x}H{text}")

def get_term_size():
    try:
        res = subprocess.check_output(['stty', 'size'], stderr=subprocess.DEVNULL).decode().split()
        return int(res[0]), int(res[1])
    except:
        return 24, 80

def get_layout(rows):
    logo_lines = logo_text.strip('\n').split('\n')
    logo_height = len(logo_lines)
    text_height = len(welcome_text)
    box_height = 5
    
    if rows >= (logo_height + 2 + text_height + 2 + box_height + 4):
        total_height = logo_height + 2 + text_height + 2 + box_height
        start_y = max(3, (rows - total_height) // 2)
        text_y = start_y + logo_height + 2
        box_y = text_y + text_height + 2
        show_text = True
    else:
        total_height = logo_height + 3 + box_height
        start_y = max(3, (rows - total_height) // 2)
        text_y = 0
        box_y = start_y + logo_height + 3
        show_text = False
        
    return start_y, text_y, box_y, show_text, logo_lines

def draw_static_ui():
    rows, cols = get_term_size()
    sys.stdout.write("\033[2J\033[H")
    
    color = "\033[1;32m" # Emerald green borders
    draw_at(1, 1, color + "╔" + "═"*(cols-2) + "╗\033[0m")
    sys.stdout.flush()
    time.sleep(0.02)
    
    for r in range(2, rows):
        draw_at(r, 1, color + "║\033[0m")
        draw_at(r, cols, color + "║\033[0m")
        sys.stdout.flush()
        time.sleep(0.002)
        
    draw_at(rows, 1, color + "╚" + "═"*(cols-2) + "╝\033[0m")
    sys.stdout.flush()
    
    title = "[ X64 SECURE TERMINAL ]"
    draw_at(1, max(1, (cols - len(title)) // 2 + 1), f"\033[1;36m{title}\033[0m")
    
    start_y, text_y, box_y, show_text, logo_lines = get_layout(rows)
    logo_width = 83 
    
    for i, line in enumerate(logo_lines):
        x = max(2, (cols - logo_width) // 2 + 1)
        draw_at(start_y + i, x, line)
        sys.stdout.flush()
        time.sleep(0.04)
        
    if show_text:
        for i, text_line in enumerate(welcome_text):
            clean_line = text_line.replace('\033[1;36m', '').replace('\033[1;37m', '').replace('\033[1;90m', '').replace('\033[1;33m', '').replace('\033[1;32m', '').replace('\033[0m', '')
            x = max(2, (cols - len(clean_line)) // 2 + 1)
            draw_at(text_y + i, x, text_line)
            sys.stdout.flush()
            time.sleep(0.02)
        
    box_width = 72
    box_x = max(2, (cols - box_width) // 2 + 1)
    
    # Animar apertura del modal
    center_x = box_x + box_width // 2
    draw_at(box_y, center_x, "\033[1;36m+\033[0m")
    sys.stdout.flush()
    time.sleep(0.1)
    
    box_title = "[ SECURITY CLEARANCE REQUIRED ]"
    title_start = (box_width - len(box_title)) // 2
    
    top_border = f"╭{'─'*title_start}\033[1;32m{box_title}\033[1;36m{'─'*(box_width - 2 - title_start - len(box_title))}╮"
    draw_at(box_y, box_x, f"\033[1;36m{top_border}\033[0m")
    draw_at(box_y+1, box_x, f"\033[1;36m│\033[0m" + " "*(box_width-2) + f"\033[1;36m│\033[0m")
    draw_at(box_y+2, box_x, f"\033[1;36m│\033[0m" + " "*(box_width-2) + f"\033[1;36m│\033[0m")
    draw_at(box_y+3, box_x, f"\033[1;36m│\033[0m" + " "*(box_width-2) + f"\033[1;36m│\033[0m")
    draw_at(box_y+4, box_x, f"\033[1;36m╰{'─'*(box_width-2)}╯\033[0m")
    
    footer_text = " [ OMARCHY + CACHYOS // CORE SYSTEM OVERRIDE ] "
    draw_at(rows - 2, max(2, (cols - len(footer_text)) // 2 + 1), f"\033[1;32m{footer_text}\033[0m")
    
    sys.stdout.flush()

def update_dynamic_ui(password_len, msg="", scramble_char=None, is_error=False):
    rows, cols = get_term_size()
    _, _, box_y, _, _ = get_layout(rows)
    
    box_width = 72
    box_x = max(2, (cols - box_width) // 2 + 1)
    
    # Error visual feedback
    if is_error:
        box_title = "[ ACCESS DENIED ]"
        title_start = (box_width - len(box_title)) // 2
        top_border = f"╭{'─'*title_start}\033[1;31m{box_title}\033[1;31m{'─'*(box_width - 2 - title_start - len(box_title))}╮"
        draw_at(box_y, box_x, f"\033[1;31m{top_border}\033[0m")
        draw_at(box_y+1, box_x, f"\033[1;31m│\033[0m" + " "*(box_width-2) + f"\033[1;31m│\033[0m")
        draw_at(box_y+3, box_x, f"\033[1;31m│\033[0m" + " "*(box_width-2) + f"\033[1;31m│\033[0m")
        draw_at(box_y+4, box_x, f"\033[1;31m╰{'─'*(box_width-2)}╯\033[0m")
    else:
        # Restore normal box
        box_title = "[ SECURITY CLEARANCE REQUIRED ]"
        title_start = (box_width - len(box_title)) // 2
        top_border = f"╭{'─'*title_start}\033[1;32m{box_title}\033[1;36m{'─'*(box_width - 2 - title_start - len(box_title))}╮"
        draw_at(box_y, box_x, f"\033[1;36m{top_border}\033[0m")
        draw_at(box_y+1, box_x, f"\033[1;36m│\033[0m" + " "*(box_width-2) + f"\033[1;36m│\033[0m")
        draw_at(box_y+3, box_x, f"\033[1;36m│\033[0m" + " "*(box_width-2) + f"\033[1;36m│\033[0m")
        draw_at(box_y+4, box_x, f"\033[1;36m╰{'─'*(box_width-2)}╯\033[0m")

    border_char = "\033[1;31m│\033[0m" if is_error else "\033[1;36m│\033[0m"
    prompt = "  > INPUT_KEY: ["
    
    if scramble_char and password_len > 0:
        stars = "*" * (password_len - 1) + f"\033[1;32m{scramble_char}\033[1;31m"
    else:
        stars = "*" * password_len
        
    visual_stars = "*" * password_len
    space_left = max(0, 30 - len(visual_stars))
    
    content = f"\033[1;37m{prompt} \033[1;31m{stars}\033[0m{' '*space_left}\033[1;37m]\033[0m"
    content_len_visual = len(prompt) + 1 + 30 + 1
    pad_left = (box_width - 2 - content_len_visual) // 2
    
    blank_inner = " " * (box_width - 2)
    draw_at(box_y+2, box_x, border_char)
    draw_at(box_y+2, box_x + 1, blank_inner)
    draw_at(box_y+2, box_x + 1 + pad_left, content)
    draw_at(box_y+2, box_x + box_width - 1, border_char)
    
    # Blank msg space
    draw_at(box_y+5, 2, " " * (cols - 4))
    if msg:
        msg_clean = msg.replace('\033[1;33m', '').replace('\033[1;31m', '').replace('\033[1;32m', '').replace('\033[1;36m', '').replace('\033[0m', '')
        pad_msg = max(2, (cols - len(msg_clean)) // 2 + 1)
        draw_at(box_y+6, pad_msg, msg)
        
    sys.stdout.flush()

def show_loading_bar(password_len):
    rows, cols = get_term_size()
    _, _, box_y, _, _ = get_layout(rows)
    box_width = 72
    box_x = max(2, (cols - box_width) // 2 + 1)
    
    for progress in range(1, 101, random.randint(15, 30)):
        if progress > 100: progress = 100
        bar_len = 30
        filled = int((progress / 100) * bar_len)
        bar = "\033[1;36m█\033[0m" * filled + "\033[1;90m░\033[0m" * (bar_len - filled)
        
        content = f"\033[1;37m  > DECRYPTING: [{bar}\033[1;37m] {progress}%\033[0m"
        pad_left = (box_width - 2 - (18 + bar_len + 5)) // 2
        
        blank_inner = " " * (box_width - 2)
        draw_at(box_y+2, box_x + 1, blank_inner)
        draw_at(box_y+2, box_x + 1 + pad_left, content)
        
        draw_at(box_y+6, 2, " " * (cols - 4))
        msg = f"\033[1;36m[!] VERIFYING CREDENTIALS...\033[0m"
        msg_clean = "[!] VERIFYING CREDENTIALS..."
        pad_msg = max(2, (cols - len(msg_clean)) // 2 + 1)
        draw_at(box_y+6, pad_msg, msg)
        
        sys.stdout.flush()
        time.sleep(random.uniform(0.05, 0.15))
        
    # Ensure it reaches 100%
    bar = "\033[1;36m█\033[0m" * 30
    content = f"\033[1;37m  > DECRYPTING: [{bar}\033[1;37m] 100%\033[0m"
    pad_left = (box_width - 2 - (18 + 30 + 5)) // 2
    draw_at(box_y+2, box_x + 1, " " * (box_width - 2))
    draw_at(box_y+2, box_x + 1 + pad_left, content)
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
                        
                        sys.stdout.write("\033[2K") # Clear line
                        show_loading_bar(len(password))
                        
                        proc = subprocess.Popen(
                            ['sudo', '-S', '-v'],
                            stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE
                        )
                        out, err = proc.communicate(input=(password + '\n').encode())
                        
                        if proc.returncode == 0:
                            update_dynamic_ui(len(password), "\033[1;32m[✓] ACCESS GRANTED. INITIATING METAMORPHOSIS...\033[0m")
                            time.sleep(1)
                            sys.stdout.write("\033[2J\033[H\033[?25h") 
                            sys.exit(0)
                        else:
                            password = ""
                            msg = "\033[1;31m[X] ACCESS DENIED. INCORRECT KEY.\033[0m"
                            update_dynamic_ui(len(password), msg, is_error=True)
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
                        if len(password) == 0:
                            # Reset error state if any
                            update_dynamic_ui(0, "")
                        password += ch
                        
                        scramble_chars = "!@#$%^&*?/~X"
                        for _ in range(2):
                            update_dynamic_ui(len(password), "", scramble_char=random.choice(scramble_chars))
                            time.sleep(0.015)
                        update_dynamic_ui(len(password), "")
                        
                        break
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        sys.stdout.write("\033[?25h")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.stdout.write("\033[?25h\033[2J\033[H")
        sys.exit(1)
