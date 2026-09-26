#!/bin/bash
echo "Verifying Elsewhen plugin installation..."
packaged_plugin="/usr/share/omarchy/shell/plugins/omacom.elsewhen"

# If pacman thinks it's installed but the directory is missing (due to git resets), reinstall it
if pacman -Q elsewhen >/dev/null 2>&1 && [[ ! -d $packaged_plugin ]]; then
    echo "Elsewhen package is installed but files are missing. Forcing reinstallation..."
    sudo pacman -S --noconfirm elsewhen
fi

omarchy-shell -q shell rescanPlugins
omarchy-bar put omacom.elsewhen --before omarchy.clock
