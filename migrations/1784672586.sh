echo "X64 Override: Canceling switch to quickshell-git to prevent CachyOS noctalia-qs conflict"

# X64 Omarchy: We intentionally keep standard quickshell.
# Installing quickshell-git on CachyOS pulls 'noctalia-qs', breaking the shell.
# if ! omarchy-pkg-present quickshell-git; then
#   # One transaction with --ask 4 so pacman accepts replacing the conflicting
#   # quickshell package in place; packages depending on quickshell stay
#   # satisfied through the provides.
#   sudo pacman -S --noconfirm --ask 4 quickshell-git
# fi
