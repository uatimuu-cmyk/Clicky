#!/usr/bin/env python3
"""Generate the Clicky SVG logo files (pure geometry, no fonts, no raster data).

Optional: the shipped SVGs in assets/ are the editable source of truth.
Running this script regenerates them from scratch and overwrites hand edits.
"""
from pathlib import Path

CHAR, GREY, WHITE, LIME = "#171717", "#242424", "#E5E5E5", "#D6FF00"
OUT = Path(__file__).resolve().parent.parent / "assets"


def pts(points, dx=0, dy=0, s=1.0):
    return " ".join(f"{'M' if i == 0 else 'L'}{x * s + dx:g} {y * s + dy:g}"
                    for i, (x, y) in enumerate(points)) + " Z"


# ---------------------------------------------------------------- icon (512 grid)
C_ICON = [(404, 104), (112, 104), (112, 376), (252, 376), (252, 300),
          (190, 300), (190, 180), (404, 180)]
CURSOR = [(0, 0), (0, 162), (42, 124), (72, 190), (102, 177), (73, 112), (126, 112)]
CUR_DX, CUR_DY = 290, 226


def icon_body(detail=True):
    """Tile + glyph as SVG elements on a 512x512 canvas."""
    rim = f'<rect x="24" y="24" width="464" height="464" rx="64" fill="{GREY}"/>' if detail else ""
    inset = 44 if detail else 24
    size = 512 - 2 * inset
    rx = 44 if detail else 64
    tile = f'<rect x="{inset}" y="{inset}" width="{size}" height="{size}" rx="{rx}" fill="{CHAR}"/>'
    c = f'<path d="{pts(C_ICON)}" fill="{LIME}"/>'
    cur = pts(CURSOR, CUR_DX, CUR_DY)
    cut = (f'<path d="{cur}" fill="{CHAR}" stroke="{CHAR}" stroke-width="36" '
           f'stroke-linejoin="round"/>')
    cursor = f'<path d="{cur}" fill="{WHITE}"/>'
    return "\n  ".join(e for e in [rim, tile, c, cut, cursor] if e)


def icon_svg(detail=True):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512">
  <title>Clicky icon</title>
  {icon_body(detail)}
</svg>
'''


# ---------------------------------------------------------------- wordmark
T = 44  # stroke weight
TOP, XH, BASE, DESC = 40, 110, 260, 330


def letters():
    C = ([(150, TOP), (0, TOP), (0, BASE), (150, BASE), (150, BASE - T), (T, BASE - T),
          (T, TOP + T), (150, TOP + T)], 150)
    L = ([(0, TOP), (T, TOP), (T, BASE), (0, BASE)], T)
    I_STEM = ([(0, XH), (T, XH), (T, BASE), (0, BASE)], T)
    I_DOT = ([(0, TOP), (T, TOP), (T, TOP + T), (0, TOP + T)], T)
    c = ([(120, XH), (0, XH), (0, BASE), (120, BASE), (120, BASE - T), (T, BASE - T),
          (T, XH + T), (120, XH + T)], 120)
    k = ([(0, TOP), (T, TOP), (T, 178), (86, XH), (140, XH), (88, 190), (142, BASE),
          (88, BASE), (56, 226), (T, 236), (T, BASE), (0, BASE)], 142)
    y = ([(0, XH), (T, XH), (T, 172), (74, 172), (74, XH), (118, XH), (118, DESC),
          (14, DESC), (14, DESC - T), (74, DESC - T), (74, 216), (0, 216)], 118)
    return C, L, I_STEM, I_DOT, c, k, y


def wordmark_elements(text_colour, scale, ox, oy):
    C, L, I_STEM, I_DOT, c, k, y = letters()
    gap, x, els = 30, 0, []

    def add(g, colour):
        els.append(f'<path d="{pts(g[0], ox + x * scale, oy, scale)}" fill="{colour}"/>')

    add(C, text_colour); x += C[1] + gap
    add(L, text_colour); x += L[1] + gap
    add(I_STEM, text_colour)
    add(I_DOT, LIME); x += I_STEM[1] + gap
    add(c, text_colour); x += c[1] + gap
    add(k, text_colour); x += k[1] + gap
    add(y, text_colour); x += y[1]
    return els, x * scale


def logo_svg(text_colour):
    s, ox, oy = 1.3, 560, 16
    els, width = wordmark_elements(text_colour, s, ox, oy)
    total_w = int(ox + width + 40)
    body = "\n".join("    " + e for e in els)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {total_w} 512" width="{total_w}" height="512">
  <title>Clicky</title>
  <g id="icon">
  {icon_body(True)}
  </g>
  <g id="wordmark">
{body}
  </g>
</svg>
'''


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    (OUT / "clicky-icon.svg").write_text(icon_svg(True))
    (OUT / "clicky-icon-small.svg").write_text(icon_svg(False))
    (OUT / "clicky.svg").write_text(logo_svg(WHITE))
    (OUT / "clicky-on-light.svg").write_text(logo_svg(CHAR))
    print("written")
