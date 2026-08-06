echo "Replace GNOME Calculator with Omacalc"

omarchy-pkg-present gnome-calculator || omarchy-pkg-add gnome-calculator
omarchy-pkg-present omacalc && omarchy-pkg-drop omacalc || true
