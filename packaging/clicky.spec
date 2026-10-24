# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for Clicky. Driven by build.sh, which sets:
#   CLICKY_ENTRY   absolute path to Clicky's main .py file (required)
#   CLICKY_ONEFILE "1" for a single-file executable, otherwise a folder build
import os
import sys
from pathlib import Path

ROOT = Path(SPECPATH).resolve().parent          # Clicky-Branding/
ENTRY = os.environ.get("CLICKY_ENTRY", "").strip()
if not ENTRY or not Path(ENTRY).is_file():
    sys.exit("CLICKY_ENTRY is not set or is not a file. Run ./build.sh --entry /path/to/clicky.py")
ENTRY = Path(ENTRY).resolve()
ONEFILE = os.environ.get("CLICKY_ONEFILE") == "1"

# Files bundled next to the app. In the frozen app they live under sys._MEIPASS/assets
# (onefile) or <install dir>/_internal/assets (onedir, PyInstaller >= 6).
datas = [
    (str(ROOT / "assets" / "clicky-icon.svg"), "assets"),
    (str(ROOT / "assets" / "clicky-icon.png"), "assets"),
    (str(ROOT / "assets" / "clicky.svg"), "assets"),
    (str(ROOT / "assets" / "clicky.png"), "assets"),
    (str(ROOT / "assets" / "icons"), "assets/icons"),
]
# If Clicky loads other data files (.ui, .json defaults, sounds...), add them here:
# datas += [("/abs/path/to/file_or_dir", "dest/dir/inside/bundle")]



def static_submodules(package):
    """List a package's submodules by walking its files, WITHOUT importing them.

    PyInstaller's collect_submodules() imports every module, and pynput's X11
    backends refuse to import when no display is available (SSH, TTY, CI), so
    they would silently be left out of the bundle.
    """
    import importlib.util
    spec = importlib.util.find_spec(package)
    if spec is None or not spec.submodule_search_locations:
        return []
    names = [package]
    for loc in spec.submodule_search_locations:
        loc = Path(loc)
        for f in loc.rglob("*.py"):
            rel = f.relative_to(loc).with_suffix("")
            parts = rel.parts[:-1] if rel.name == "__init__" else rel.parts
            names.append(".".join((package, *parts)) if parts else package)
    return sorted(set(names))


# pynput picks its backend (X11 / uinput) at runtime, so bundle all of them,
# plus python-xlib which the X11 backend needs. evdev is only needed by the
# optional uinput backend and is skipped if not installed.
hiddenimports = static_submodules("pynput") + static_submodules("Xlib") + static_submodules("evdev")

a = Analysis(
    [str(ENTRY)],
    pathex=[str(ENTRY.parent)],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=["tkinter"],
    noarchive=False,
)
pyz = PYZ(a.pure)

if ONEFILE:
    exe = EXE(
        pyz, a.scripts, a.binaries, a.datas, [],
        name="clicky", debug=False, strip=False, upx=False, console=False,
    )
else:
    exe = EXE(
        pyz, a.scripts, [],
        exclude_binaries=True,
        name="clicky", debug=False, strip=False, upx=False, console=False,
    )
    coll = COLLECT(
        exe, a.binaries, a.datas,
        strip=False, upx=False, name="clicky",
    )
