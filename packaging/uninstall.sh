#!/usr/bin/env bash
# Remove only the files install.sh created. Your Clicky settings/profiles are left alone.
set -euo pipefail

DATA="${XDG_DATA_HOME:-$HOME/.local/share}"
APP_DIR="$HOME/.local/opt/clicky"

case "$APP_DIR" in
  "$HOME"/.local/opt/clicky) ;;
  *) echo "Refusing unexpected install dir: $APP_DIR" >&2; exit 1 ;;
esac

echo "==> Removing application"
rm -rf "$APP_DIR"
rmdir "$HOME/.local/opt" 2>/dev/null || true   # only if now empty

echo "==> Removing launcher"
rm -f "$DATA/applications/clicky.desktop"

echo "==> Removing icons"
rm -f "$DATA"/icons/hicolor/*/apps/clicky.png "$DATA/icons/hicolor/scalable/apps/clicky.svg"

echo "==> Refreshing desktop caches"
command -v update-desktop-database >/dev/null && update-desktop-database "$DATA/applications" 2>/dev/null || true
if [[ -f "$DATA/icons/hicolor/index.theme" ]] && command -v gtk-update-icon-cache >/dev/null; then
  gtk-update-icon-cache -q -f -t "$DATA/icons/hicolor" || true
fi
touch "$DATA/icons/hicolor" 2>/dev/null || true
if command -v kbuildsycoca6 >/dev/null; then kbuildsycoca6 --noincremental >/dev/null 2>&1 || true
elif command -v kbuildsycoca5 >/dev/null; then kbuildsycoca5 --noincremental >/dev/null 2>&1 || true; fi

echo
echo "Clicky uninstalled. Settings and profiles were not touched"
echo "(wherever Clicky stores them, typically under ~/.config or ~/.local/share)."
