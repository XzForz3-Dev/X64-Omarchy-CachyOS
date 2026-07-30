import json
from collections import deque
from rich.console import Console

LOG_FILE = "x64-install.log"
console = Console()

log_lines = deque(maxlen=25)
install_error = None
install_done = False
start_time = None
end_time = None

current_state = "menu" # menu, working, error, done
ui_transitioned = False

error_prompt = None
error_response = None

with open("core/menu_data.json", "r", encoding="utf-8") as f:
    menu_data = json.load(f)

active_pane = "left"
cat_idx = 0
item_idx = 0
user_choices = {"theme": "Tokyo Night", "drivers": "Mesa (AMD/Intel)", "packages": []}
transition_text = ""
is_legacy_nvidia = False
has_nvidia = False
