#!/usr/bin/env bash
# Per-user install of Clicky (no root). Installs:
#   app        ~/.local/opt/clicky/
#   launcher   ~/.local/share/applications/clicky.desktop
#   icons      ~/.local/share/icons/hicolor/<size>x<size>/apps/clicky.png  (+ scalable svg)
# Never touches your Clicky settings or profiles.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$HERE")"
DATA="${XDG_DATA_HOME:-$HOME/.local/share}"
APP_DIR="$HOME/.local/opt/clicky"
BUILD="${1:-$ROOT/dist/clicky}"

if [[ -d "$BUILD" && -x "$BUILD/clicky" ]]; then
  KIND=dir
elif [[ -f "$BUILD" && -x "$BUILD" ]]; then
  KIND=file
else
  echo "No build found at $BUILD. Run ./build.sh first." >&2
  exit 1
fi

# Safety: only ever replace our own directory.
case "$APP_DIR" in
  "$HOME"/.local/opt/clicky) ;;
  *) echo "Refusing unexpected install dir: $APP_DIR" >&2; exit 1 ;;
esac

echo "==> Installing application to $APP_DIR"
rm -rf "$APP_DIR"
mkdir -p "$APP_DIR"
if [[ $KIND == dir ]]; then cp -a "$BUILD"/. "$APP_DIR"/; else install -m 755 "$BUILD" "$APP_DIR/clicky"; fi

echo "==> Installing icons"
for png in "$ROOT"/assets/icons/clicky-*.png; do
  size="$(basename "$png" .png)"; size="${size#clicky-}"
  dest="$DATA/icons/hicolor/${size}x${size}/apps"
  mkdir -p "$dest"
  install -m 644 "$png" "$dest/clicky.png"
done
mkdir -p "$DATA/icons/hicolor/scalable/apps"
install -m 644 "$ROOT/assets/clicky-icon.svg" "$DATA/icons/hicolor/scalable/apps/clicky.svg"

echo "==> Installing launcher"
mkdir -p "$DATA/applications"
sed "s|@EXEC@|$APP_DIR/clicky|g" "$HERE/clicky.desktop.in" > "$DATA/applications/clicky.desktop"
chmod 644 "$DATA/applications/clicky.desktop"
if command -v desktop-file-validate >/dev/null; then
  desktop-file-validate "$DATA/applications/clicky.desktop" || echo "    (validator warnings above are usually harmless)"
fi

echo "==> Refreshing desktop caches"
command -v update-desktop-database >/dev/null && update-desktop-database "$DATA/applications" 2>/dev/null || true
if [[ -f "$DATA/icons/hicolor/index.theme" ]] && command -v gtk-update-icon-cache >/dev/null; then
  gtk-update-icon-cache -q -f -t "$DATA/icons/hicolor" || true
fi
touch "$DATA/icons/hicolor" 2>/dev/null || true
if command -v kbuildsycoca6 >/dev/null; then kbuildsycoca6 --noincremental >/dev/null 2>&1 || true
elif command -v kbuildsycoca5 >/dev/null; then kbuildsycoca5 --noincremental >/dev/null 2>&1 || true; fi

echo
echo "Clicky installed. Find it in the KDE application menu (Utilities), or run: $APP_DIR/clicky"
echo "If the menu entry or icon does not appear yet, log out and back in."
