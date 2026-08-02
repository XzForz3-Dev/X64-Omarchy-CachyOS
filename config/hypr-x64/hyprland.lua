-- ----------------------------------------------------- 
-- Hyprland X64 Studios (Barebones Base en Lua)
-- ----------------------------------------------------- 

-- Variables de Entorno Base
hl.env("XCURSOR_SIZE", "24")
hl.env("HYPRCURSOR_SIZE", "24")

-- Monitor
hl.config({
  
  monitor = {
    ",preferred,auto,1"
  },
  
  general = {
    gaps_in = 5,
    gaps_out = 20,
    border_size = 2,
    ["col.active_border"] = "rgba(33ccffee)",
    ["col.inactive_border"] = "rgba(595959aa)",
    resize_on_border = false,
    allow_tearing = false,
    layout = "dwindle"
  },

  decoration = {
    rounding = 10,
    blur = {
      enabled = true,
      size = 3,
      passes = 1,
      vibrancy = 0.1696
    }
  },

  animations = {
    enabled = true,
    bezier = {
      "easeOutQuint,0.23,1,0.32,1",
      "easeInOutCubic,0.65,0.05,0.36,1",
      "linear,0,0,1,1",
      "almostLinear,0.5,0.5,0.75,1.0",
      "quick,0.15,0,0.1,1"
    },
    animation = {
      "global, 1, 10, default",
      "border, 1, 5.39, easeOutQuint",
      "windows, 1, 4.79, easeOutQuint",
      "windowsIn, 1, 4.1, easeOutQuint, popin 87%",
      "windowsOut, 1, 1.49, linear, popin 87%",
      "fadeIn, 1, 1.73, almostLinear",
      "fadeOut, 1, 1.49, almostLinear",
      "fade, 1, 3.03, quick",
      "workspaces, 1, 1.94, almostLinear, fade"
    }
  },

  input = {
    kb_layout = "us",
    follow_mouse = 1,
    sensitivity = 0
  }
})

-- Keybindings
local terminal = "alacritty"
local fileManager = "dolphin"

hl.bind("SUPER + Return", hl.dsp.exec_cmd(terminal))
hl.bind("SUPER + Q", hl.dsp.window.close())
hl.bind("SUPER + M", hl.dsp.exit())
hl.bind("SUPER + E", hl.dsp.exec_cmd(fileManager))
hl.bind("SUPER + V", hl.dsp.window.float({ action = "toggle" }))

-- Workspaces
hl.bind("SUPER + 1", hl.dsp.focus({ workspace = 1 }))
hl.bind("SUPER + 2", hl.dsp.focus({ workspace = 2 }))
hl.bind("SUPER + 3", hl.dsp.focus({ workspace = 3 }))
hl.bind("SUPER + 4", hl.dsp.focus({ workspace = 4 }))

hl.bind("SUPER + SHIFT + 1", hl.dsp.window.move({ workspace = 1 }))
hl.bind("SUPER + SHIFT + 2", hl.dsp.window.move({ workspace = 2 }))
hl.bind("SUPER + SHIFT + 3", hl.dsp.window.move({ workspace = 3 }))
hl.bind("SUPER + SHIFT + 4", hl.dsp.window.move({ workspace = 4 }))
