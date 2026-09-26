#!/bin/bash

# omarchy:summary=Migrate existing Omarchy SDDM installations to X64 Studios

set -euo pipefail

# Ensure SDDM directories exist
sudo mkdir -p /usr/share/sddm/themes/x64-studios /etc/sddm.conf.d /var/lib/sddm

# Copy the rebranded theme from the repository
sudo cp -r "$OMARCHY_PATH/default/sddm/x64-studios/"* /usr/share/sddm/themes/x64-studios/ 2>/dev/null || true

# If the system is currently using the old omarchy theme, switch it to x64-studios
if grep -q "Current=omarchy" /etc/sddm.conf.d/omarchy.conf 2>/dev/null || grep -q "Current=omarchy" /etc/sddm.conf 2>/dev/null; then
    echo -e "[Theme]\nCurrent=x64-studios" | sudo tee /etc/sddm.conf.d/x64-studios.conf >/dev/null
    sudo rm -f /etc/sddm.conf.d/omarchy.conf
fi

# Clean up the old omarchy SDDM theme if it exists
sudo rm -rf /usr/share/sddm/themes/omarchy
