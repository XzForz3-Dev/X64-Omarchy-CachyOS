-- Learn how to configure Hyprland: https://wiki.hypr.land/Configuring/Start/

-- Omarchy's bootstrap keeps path setup out of this user config.
dofile((os.getenv("OMARCHY_PATH") or "/usr/share/omarchy") .. "/default/hypr/bootstrap.lua")

-- Disable all Omarchy default bindings. Add your own in hypr/bindings.lua.
-- omarchy_default_bindings = false
--
-- Or disable only bindings for Omarchy's preinstalled apps/web apps while
-- keeping core window-manager bindings:
-- omarchy_preinstalled_bindings = false

-- Load Omarchy defaults.
require("default.hypr.omarchy")

-- Put your personal overrides in these files. They're loaded after Omarchy's
-- defaults so package updates can improve the defaults without rewriting your
-- ~/.config/hypr files.
require("hypr.monitors")
require("hypr.input")
require("hypr.bindings")
require("hypr.looknfeel")
require("hypr.autostart")

-- Toggle config flags dynamically.
require("default.hypr.toggles")

-- Add any other personal Hyprland configuration below.
-- o.window("qemu", { workspace = "5" })

-- X64 Studios: Modo Gaming Automático (Cero Latencia)
hl.command("windowrulev2 = immediate, class:^steam_app_.*$")
hl.command("windowrulev2 = noanim, class:^steam_app_.*$")
hl.command("windowrulev2 = noblur, class:^steam_app_.*$")
hl.command("windowrulev2 = noshadow, class:^steam_app_.*$")

hl.command("windowrulev2 = immediate, class:^gamescope$")
hl.command("windowrulev2 = noanim, class:^gamescope$")
hl.command("windowrulev2 = noblur, class:^gamescope$")
hl.command("windowrulev2 = noshadow, class:^gamescope$")

hl.command("windowrulev2 = immediate, class:^cs2$")
hl.command("windowrulev2 = noanim, class:^cs2$")
hl.command("windowrulev2 = noblur, class:^cs2$")
hl.command("windowrulev2 = noshadow, class:^cs2$")

-- Hardware Video Acceleration (VA-API) Environment Variables
hl.env("MOZ_ENABLE_WAYLAND", "1")
hl.env("MOZ_DISABLE_RDD_SANDBOX", "1")
hl.env("NVD_BACKEND", "direct") -- Para compatibilidad de hardware NVIDIA
