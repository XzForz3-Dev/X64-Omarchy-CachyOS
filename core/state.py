import json
from collections import deque

log_lines = deque(maxlen=25)
install_error = None
install_done = False
start_time = None
end_time = None

current_state = "menu" # menu, working, error, done
ui_transitioned = False

error_prompt = None
error_response = None

active_pane = "left"
cat_idx = 0
item_idx = 0
user_choices = {"theme": "Tokyo Night", "drivers": "Mesa (AMD/Intel)", "packages": []}
transition_text = ""

with open("core/menu_data.json", "r", encoding="utf-8") as f:
    menu_data = json.load(f)
