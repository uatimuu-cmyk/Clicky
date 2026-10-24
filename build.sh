#!/usr/bin/env bash
# Build Clicky into a standalone Linux application with PyInstaller.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$ROOT/.venv-build"
ENTRY="${CLICKY_ENTRY:-}"
ONEFILE=0
CLEAN=0
SITE=0

usage() {
  cat <<USAGE
Usage: ./build.sh [--entry /path/to/clicky.py] [--onefile] [--clean] [--system-site-packages]

  --entry FILE             Clicky's main Python file (or set CLICKY_ENTRY).
                           Auto-detected if ../clicky.py, ../main.py etc. exists.
  --onefile                Build one self-extracting executable instead of a folder.
  --clean                  Delete dist/, build/ and the build venv first.
  --system-site-packages   Let the build venv see system Python packages
                           (e.g. PySide6 installed with pacman) instead of pip-installing them.

Output: dist/clicky/clicky   (folder build)   or   dist/clicky   (single file)
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --entry) ENTRY="${2:?--entry needs a file}"; shift 2 ;;
    --onefile) ONEFILE=1; shift ;;
    --clean) CLEAN=1; shift ;;
    --system-site-packages) SITE=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage; exit 2 ;;
  esac
done

if [[ -z "$ENTRY" ]]; then
  for cand in "$ROOT/../clicky.py" "$ROOT/../Clicky.py" "$ROOT/../main.py" "$ROOT/../app.py" \
              "$ROOT/clicky.py" "$ROOT/main.py"; do
    if [[ -f "$cand" ]]; then ENTRY="$cand"; break; fi
  done
fi
if [[ -z "$ENTRY" || ! -f "$ENTRY" ]]; then
  echo "Could not find Clicky's main Python file." >&2
  echo "Run:  ./build.sh --entry /path/to/clicky.py" >&2
  exit 1
fi
ENTRY="$(cd "$(dirname "$ENTRY")" && pwd)/$(basename "$ENTRY")"
echo "==> Entry point: $ENTRY"

command -v python3 >/dev/null || { echo "python3 not found (sudo pacman -S python)" >&2; exit 1; }

if [[ $CLEAN -eq 1 ]]; then
  echo "==> Cleaning previous build output"
  rm -rf "$ROOT/dist" "$ROOT/build" "$VENV"
fi

if [[ ! -x "$VENV/bin/python" ]]; then
  echo "==> Creating build virtualenv"
  if [[ $SITE -eq 1 ]]; then python3 -m venv --system-site-packages "$VENV"; else python3 -m venv "$VENV"; fi
fi
# shellcheck disable=SC1091
source "$VENV/bin/activate"

REQ="$(dirname "$ENTRY")/requirements.txt"
echo "==> Installing build dependencies"
python -m pip install --quiet --upgrade pip
python -m pip install --quiet --upgrade pyinstaller
if [[ $SITE -eq 0 ]]; then
  if [[ -f "$REQ" ]]; then
    echo "    using $REQ"
    python -m pip install --quiet -r "$REQ"
  else
    python -m pip install --quiet PySide6 pynput
  fi
fi

# Folder and single-file builds both write dist/clicky, so never mix them.
rm -rf "$ROOT/dist/clicky"

echo "==> Running PyInstaller ($([[ $ONEFILE -eq 1 ]] && echo single-file || echo folder) build)"
CLICKY_ENTRY="$ENTRY" CLICKY_ONEFILE="$ONEFILE" \
  pyinstaller --noconfirm --clean \
    --distpath "$ROOT/dist" --workpath "$ROOT/build/pyinstaller" \
    "$ROOT/packaging/clicky.spec"

if [[ $ONEFILE -eq 1 ]]; then OUT="$ROOT/dist/clicky"; else OUT="$ROOT/dist/clicky/clicky"; fi
[[ -x "$OUT" ]] || { echo "Build finished but $OUT is missing" >&2; exit 1; }

echo
echo "Build complete: $OUT"
echo "Test it:    $OUT"
echo "Install it: ./packaging/install.sh"
