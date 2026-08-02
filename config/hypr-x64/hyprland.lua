-- ----------------------------------------------------- 
-- Hyprland X64 Studios (Barebones Base en Lua)
-- ----------------------------------------------------- 

-- Variables de Entorno Base
hl.env("XCURSOR_SIZE", "24")
hl.env("HYPRCURSOR_SIZE", "24")

-- Autostart (Servicios Críticos)
hl.on("hyprland.start", function()
  hl.exec_cmd("/usr/lib/polkit-kde-authentication-agent-1")
  hl.exec_cmd("dbus-update-activation-environment --systemd WAYLAND_DISPLAY XDG_CURRENT_DESKTOP")
  hl.exec_cmd("swaync -s $HOME/.config/swaync/style.css -c $HOME/.config/swaync/config.json")
  hl.exec_cmd("swayosd-server")
  hl.exec_cmd("waybar -c $HOME/.config/waybar-x64/config -s $HOME/.config/waybar-x64/style.css")
  hl.exec_cmd("hyprpaper -c $HOME/.config/hypr-x64/hyprpaper.conf")
end)

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
local launcher = "rofi -show drun"

hl.bind("SUPER + Return", hl.dsp.exec_cmd(terminal))
hl.bind("SUPER + Q", hl.dsp.window.close())
hl.bind("SUPER + M", hl.dsp.exit())
hl.bind("SUPER + E", hl.dsp.exec_cmd(fileManager))
hl.bind("SUPER + V", hl.dsp.window.float({ action = "toggle" }))
hl.bind("SUPER + D", hl.dsp.exec_cmd(launcher))
hl.bind("SUPER + N", hl.dsp.exec_cmd("swaync-client -t -sw"))
hl.bind("SUPER + L", hl.dsp.exec_cmd("hyprlock -c $HOME/.config/hypr-x64/hyprlock.conf"))
hl.bind("SUPER + Escape", hl.dsp.exec_cmd("wlogout -b 5 -c 0 -r 0 -m 0 --layout $HOME/.config/wlogout/layout --css $HOME/.config/wlogout/style.css"))

-- Workspaces
hl.bind("SUPER + 1", hl.dsp.focus({ workspace = 1 }))
hl.bind("SUPER + 2", hl.dsp.focus({ workspace = 2 }))
hl.bind("SUPER + 3", hl.dsp.focus({ workspace = 3 }))
hl.bind("SUPER + 4", hl.dsp.focus({ workspace = 4 }))

hl.bind("SUPER + SHIFT + 1", hl.dsp.window.move({ workspace = 1 }))
hl.bind("SUPER + SHIFT + 2", hl.dsp.window.move({ workspace = 2 }))
hl.bind("SUPER + SHIFT + 3", hl.dsp.window.move({ workspace = 3 }))
hl.bind("SUPER + SHIFT + 4", hl.dsp.window.move({ workspace = 4 }))

-- Multimedia & OSD (SwayOSD)
hl.bind("XF86AudioRaiseVolume", hl.dsp.exec_cmd("swayosd-client --output-volume raise"))
hl.bind("XF86AudioLowerVolume", hl.dsp.exec_cmd("swayosd-client --output-volume lower"))
hl.bind("XF86AudioMute", hl.dsp.exec_cmd("swayosd-client --output-volume mute-toggle"))
hl.bind("XF86AudioMicMute", hl.dsp.exec_cmd("swayosd-client --input-volume mute-toggle"))
hl.bind("XF86MonBrightnessUp", hl.dsp.exec_cmd("swayosd-client --brightness raise"))
hl.bind("XF86MonBrightnessDown", hl.dsp.exec_cmd("swayosd-client --brightness lower"))
