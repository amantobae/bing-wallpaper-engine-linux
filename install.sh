#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APPS_DIR="$HOME/.local/share/applications"
ICONS_DIR="$HOME/.local/share/icons/hicolor/256x256/apps"

echo "=== Installing Bing Wallpaper Manager for KDE Plasma ==="

mkdir -p "$APPS_DIR"
mkdir -p "$ICONS_DIR"

# Install icon
cp "$SCRIPT_DIR/resources/icon.png" "$ICONS_DIR/bing-wallpaper.png"

# Prepare desktop file with exact paths
DESKTOP_SRC="$SCRIPT_DIR/com.github.bing_wallpaper_kde.desktop"
DESKTOP_DEST="$APPS_DIR/com.github.bing_wallpaper_kde.desktop"

sed -e "s|Exec=.*main.py|Exec=$SCRIPT_DIR/main.py|g" \
    -e "s|Icon=.*|Icon=$ICONS_DIR/bing-wallpaper.png|g" \
    "$DESKTOP_SRC" > "$DESKTOP_DEST"

chmod +x "$SCRIPT_DIR/main.py"
chmod +x "$DESKTOP_DEST"

# Update desktop database if available
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$APPS_DIR" || true
fi

echo "✓ Application installed successfully!"
echo "✓ You can now launch 'Bing Wallpaper Manager' from your KDE application menu or KRunner (Alt+Space)."
