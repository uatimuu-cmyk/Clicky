# Clicky — branding & packaging

Dark neo-brutalist identity for **Clicky**, plus everything needed to build it as a standalone
executable and install it as a proper per-user app on CachyOS / KDE Plasma (no root needed).

```
Clicky-Branding/
├── assets/
│   ├── clicky.svg / clicky.png               wordmark lockup, for dark backgrounds (off-white text)
│   ├── clicky-on-light.svg / .png            same lockup with charcoal text, for light backgrounds
│   ├── clicky-icon.svg / clicky-icon.png     app icon (1024×1024 PNG, transparent corners)
│   ├── clicky-icon-small.svg                 simplified icon used for 16–32 px exports
│   └── icons/clicky-{16,22,24,32,48,64,128,256,512}.png
├── packaging/
│   ├── clicky.desktop.in                     launcher template
│   ├── clicky.spec                           PyInstaller spec (folder or single-file)
│   ├── install.sh / uninstall.sh             per-user install / removal
├── tools/
│   ├── export_icons.py                       re-export all PNGs from the SVGs
│   └── generate_logo.py                      optional: regenerates the SVGs from geometry
├── build.sh
└── README.md
```

## The design

- **Icon:** a heavy lime square "C" (made from the same slab geometry as the wordmark) with an
  off-white cursor sitting in its opening. The cursor has a charcoal cut-out around it so it never
  merges with the C. It sits on a charcoal tile with a dark-grey rim, which keeps the edge visible
  on dark panels while the tile itself stands out on light ones.
- **Wordmark:** hand-built blocky letterforms drawn as paths (no font needed, nothing to install).
  The dot of the "i" is lime, as a "click" marker.
- **Palette:** charcoal `#171717`, dark grey `#242424`, off-white `#E5E5E5`, electric lime `#D6FF00`.
  Flat fills only: no gradients, glows, filters, text elements or embedded rasters.
- **Small sizes:** 16–32 px use `clicky-icon-small.svg` (bigger tile, no rim) so the C and cursor
  stay readable in panels and the system tray.

## Prerequisites (CachyOS)

```bash
sudo pacman -S --needed python python-pip xcb-util-cursor
```

`xcb-util-cursor` is the library recent Qt 6 versions need for the xcb platform plugin. I'm fairly
(not 100%) sure about this; if Clicky refuses to start with a "could not load the Qt platform plugin
xcb" message, that is the first thing to check. Optional: `sudo pacman -S librsvg` if you want
`tools/export_icons.py` to render without `pip install cairosvg`.

## Build

From the `Clicky-Branding/` folder:

```bash
chmod +x build.sh packaging/*.sh
./build.sh --entry /path/to/clicky.py
```

`--entry` is optional if Clicky's main file is `../clicky.py`, `../main.py` or `../app.py`
(or set `CLICKY_ENTRY`). The script creates a private virtualenv in `.venv-build/`, installs
PyInstaller plus either your `requirements.txt` (next to the entry file) or `PySide6 pynput`,
and builds.

**Output (folder build, recommended):** `dist/clicky/clicky` — the whole `dist/clicky/` folder
is the app, with all dependencies in `dist/clicky/_internal/`.

Test it: `./dist/clicky/clicky`

### Rebuilding after you change the Python source

```bash
./build.sh --entry /path/to/clicky.py          # incremental, reuses the venv
./packaging/install.sh                         # re-install the new build
```

Add `--clean` to wipe `dist/`, `build/` and the venv first (do this if you change Python
version or after a big dependency change). If Clicky reads extra data files (`.ui`, `.json`,
sounds…), add them to the `datas` list in `packaging/clicky.spec`.

### Single-file alternative

```bash
./build.sh --entry /path/to/clicky.py --onefile     # -> dist/clicky  (one executable)
```

Limitations: every launch unpacks the whole bundle (including Qt) into `/tmp`, so startup is
noticeably slower; it uses more disk and RAM while running; bundled files are only reachable via
`sys._MEIPASS`, not next to the executable; and crashes can leave stale `/tmp/_MEI*` folders.
The folder build avoids all of these. `install.sh` handles either kind of build.

### Using the bundled logo inside Clicky (optional)

The assets are bundled under `assets/`. To load them from your code in both frozen and normal runs:

```python
import sys
from pathlib import Path

def resource_path(relative: str) -> Path:
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base / relative

# window.setWindowIcon(QIcon(str(resource_path("assets/clicky-icon.png"))))
```

(`_MEIPASS` works for both folder and single-file builds. Adjust the non-frozen path to wherever
you keep `assets/` relative to your source.)

## Install, launch, uninstall

```bash
./packaging/install.sh          # install to ~/.local (no sudo)
```

Then open the KDE application menu and look for **Clicky** (under *Utilities*), or run:

```bash
~/.local/opt/clicky/clicky
```

Where things go:

| What | Path |
|---|---|
| Application | `~/.local/opt/clicky/` |
| Launcher | `~/.local/share/applications/clicky.desktop` |
| Icons | `~/.local/share/icons/hicolor/<N>x<N>/apps/clicky.png` and `scalable/apps/clicky.svg` |

The launcher uses an absolute path to the installed executable, so it works from the menu
without a terminal or `PATH` setup. If the entry or icon doesn't show immediately, log out and in again.

```bash
./packaging/uninstall.sh        # removes only the three locations above
```

Uninstalling never touches your settings or profiles.

## Notes and caveats

- **Tested with a stand-in app, not your real Clicky.** I built, installed, launched and
  uninstalled a minimal PySide6 + pynput test app with these exact scripts (folder and single-file
  builds, in a throwaway `$HOME`). I haven't seen your source, so anything Clicky-specific (extra
  data files, other imports) is untested. I also couldn't test on a real KDE session.
- **Wayland / input:** packaging doesn't change how Clicky talks to the input system. If it works
  when you run `python clicky.py` in your session, the bundle should behave the same, but I can't
  verify that. If you currently launch it with an environment variable (for example
  `QT_QPA_PLATFORM=xcb`), put it in the launcher: change `Exec="@EXEC@"` in
  `packaging/clicky.desktop.in` to `Exec=env QT_QPA_PLATFORM=xcb "@EXEC@"` and re-run `install.sh`.
- **Window grouping:** `StartupWMClass=clicky` is my best guess for how Plasma matches Clicky's
  window to the launcher. If the taskbar shows a generic icon, run `xprop WM_CLASS` and click the
  Clicky window (XWayland), or call `app.setDesktopFileName("clicky")` early in Clicky's startup
  so Wayland sessions match `clicky.desktop`.
- **Settings location** depends on how Clicky stores them; the scripts deliberately never look there.
- **Pacman-provided Qt:** `./build.sh --system-site-packages` skips the pip install of PySide6 and
  uses your system Python packages instead. Folder size is similar either way.

## Editing the logo

The SVGs in `assets/` are plain paths, so edit them in Inkscape or by hand. After changing them:

```bash
python3 tools/export_icons.py     # needs `pip install cairosvg` or librsvg/inkscape
```

`tools/generate_logo.py` rebuilds the SVGs from scratch and overwrites hand edits; use it only if
you want to tweak the geometry numbers.
