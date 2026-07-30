hl.on("hyprland.start", function()
  -- Slow app launch fix -- set systemd vars before starting session services.
  -- Only execute if UWSM is NOT managing the session (Legacy NVIDIA fallback).
  if not os.getenv("UWSM_FINALIZE_VARNAMES") then
    hl.exec_cmd("systemctl --user import-environment $(env | cut -d'=' -f 1)")
    hl.exec_cmd("dbus-update-activation-environment --systemd --all")
  end

  hl.exec_cmd("quickshell -n -p $OMARCHY_PATH/shell")
  hl.exec_cmd("omarchy-first-run")
  hl.exec_cmd("omarchy-powerprofiles-init")
  hl.exec_cmd(o.launch("omarchy-hyprland-monitor-watch"))
  hl.exec_cmd(o.launch("udiskie --automount --no-notify --no-tray"))

  -- Run post-boot hooks after startup config has loaded.
  hl.exec_cmd("sleep 2 && omarchy-hook post-boot")
end)
