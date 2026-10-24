#!/usr/bin/env python3
"""Export PNGs from the SVG sources in assets/.

Backends (first one found wins): cairosvg (python), rsvg-convert, inkscape.
On CachyOS:  sudo pacman -S librsvg      (gives rsvg-convert)
"""
import shutil
import subprocess
import sys
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / "assets"
ICONS = ASSETS / "icons"
SIZES = (16, 22, 24, 32, 48, 64, 128, 256, 512)
SMALL_MAX = 32  # sizes <= this use the simplified icon (bigger tile, no rim)


def render(svg: Path, png: Path, width: int, height: int | None = None):
    png.parent.mkdir(parents=True, exist_ok=True)
    try:
        import cairosvg
        kw = {"output_width": width}
        if height:
            kw["output_height"] = height
        cairosvg.svg2png(url=str(svg), write_to=str(png), **kw)
        return
    except ImportError:
        pass
    if shutil.which("rsvg-convert"):
        cmd = ["rsvg-convert", "-w", str(width)] + (["-h", str(height)] if height else []) + ["-o", str(png), str(svg)]
    elif shutil.which("inkscape"):
        cmd = ["inkscape", str(svg), "-w", str(width), "-o", str(png)]
    else:
        sys.exit("No SVG renderer found. Install librsvg (rsvg-convert), inkscape, or `pip install cairosvg`.")
    subprocess.run(cmd, check=True)


def main():
    render(ASSETS / "clicky-icon.svg", ASSETS / "clicky-icon.png", 1024)
    render(ASSETS / "clicky.svg", ASSETS / "clicky.png", 2400)
    render(ASSETS / "clicky-on-light.svg", ASSETS / "clicky-on-light.png", 2400)
    for n in SIZES:
        src = ASSETS / ("clicky-icon-small.svg" if n <= SMALL_MAX else "clicky-icon.svg")
        render(src, ICONS / f"clicky-{n}.png", n)
    print("exported:", ", ".join(sorted(p.name for p in ASSETS.glob("*.png"))), "+ icons/")


if __name__ == "__main__":
    main()
