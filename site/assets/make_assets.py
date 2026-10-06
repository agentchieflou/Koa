#!/usr/bin/env python3
"""Draw the site's logo and artwork as SVG, in one theme colour (site/README.md, step 1). Stdlib only.

    python site/assets/make_assets.py                    the Teal theme, #03787C
    python site/assets/make_assets.py --accent "#498205"  any other theme's primary colour

Every image is geometry in shades of the accent (deep, mid, light, line) with no text, so it stays true when the
copy changes and never needs translating; the one exception is `request-flow`, whose words are also its alt text in
`site/pages/work-with-us.md`. SharePoint takes PNG for the logo, hero tiles and title areas: render each SVG at its
own size (any browser, or Chromium headless) and commit the PNG beside it. `tests/test_site.py` checks that every PNG
has its SVG and the SVG's size.
"""
from __future__ import annotations
import argparse
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
TEAL = "#03787C"


def _rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def mix(a: str, b: str, t: float) -> str:
    x, y = _rgb(a), _rgb(b)
    return "#" + "".join(f"{round(p * (1 - t) + q * t):02X}" for p, q in zip(x, y))


def palette(accent: str) -> dict[str, str]:
    return {"accent": accent.upper(), "deep": mix(accent, "#000000", 0.58), "mid": mix(accent, "#000000", 0.15),
            "light": mix(accent, "#FFFFFF", 0.55), "line": mix(accent, "#FFFFFF", 0.3), "soft": mix(accent, "#FFFFFF", 0.9)}


def svg(w: int, h: int, body: str, title: str) -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img">\n'
            f"  <title>{title}</title>\n{body}</svg>\n")


def crown(c: dict, x: float, y: float, s: float, ground: str, ink: str) -> str:
    """The mark: three bars that are also a crown, on a rounded square. (x, y) top left, s the side."""
    k = s / 48
    def r(a, b, w, h, rx):
        return f'<rect x="{x + a * k:.1f}" y="{y + b * k:.1f}" width="{w * k:.1f}" height="{h * k:.1f}" rx="{rx * k:.1f}" fill="{ink}"/>'
    def dot(a, b):
        return f'<circle cx="{x + a * k:.1f}" cy="{y + b * k:.1f}" r="{2.6 * k:.1f}" fill="{ink}"/>'
    return (f'  <rect x="{x}" y="{y}" width="{s}" height="{s}" rx="{10 * k:.1f}" fill="{ground}"/>\n  '
            + r(12, 21, 6, 13, 1.5) + r(21, 15, 6, 19, 1.5) + r(30, 21, 6, 13, 1.5)
            + dot(15, 16.5) + dot(24, 10.5) + dot(33, 16.5) + r(11, 36, 26, 3, 1.5) + "\n")


def dots(c: dict, x0: int, y0: int, cols: int, rows: int, gap: int, r: float = 3) -> str:
    return "".join(f'<circle cx="{x0 + i * gap}" cy="{y0 + j * gap}" r="{r}" fill="{c["line"]}" opacity="0.35"/>'
                   for j in range(rows) for i in range(cols))


def art(accent: str) -> dict[str, str]:
    c = palette(accent)
    d, m, li, ln = c["deep"], c["mid"], c["light"], c["line"]
    out = {}
    out["logo"] = svg(256, 256, crown(c, 0, 0, 256, c["accent"], "#FFFFFF"), "Data Czars")

    out["hero-main"] = svg(1600, 900, f'''  <rect width="1600" height="900" fill="{d}"/>
  <g>{dots(c, 80, 80, 12, 6, 64)}</g>
  <g stroke="{ln}" stroke-width="3" fill="none" opacity="0.85">
    <path d="M880 220 L1080 150 L1290 260 L1200 470 L990 450 Z"/><path d="M1080 150 L1200 470"/><path d="M880 220 L1200 470"/>
    <path d="M1290 260 L1420 110"/><path d="M990 450 L800 540"/>
  </g>
  <g fill="{li}"><circle cx="880" cy="220" r="16"/><circle cx="1080" cy="150" r="20"/><circle cx="1290" cy="260" r="16"/>
    <circle cx="1200" cy="470" r="26"/><circle cx="990" cy="450" r="14"/><circle cx="1420" cy="110" r="12"/><circle cx="800" cy="540" r="12"/></g>
  <g fill="{m}"><rect x="880" y="610" width="52" height="150" rx="6"/><rect x="956" y="560" width="52" height="200" rx="6"/>
    <rect x="1032" y="510" width="52" height="250" rx="6"/><rect x="1108" y="580" width="52" height="180" rx="6"/>
    <rect x="1184" y="490" width="52" height="270" rx="6"/><rect x="1260" y="540" width="52" height="220" rx="6"/></g>
''', "Data Czars: agents and data, connected")

    tiles = "".join(f'<rect x="{x}" y="{y}" width="230" height="140" rx="12" fill="{m}"/>'
                    for y in (150, 320, 490) for x in (200, 450, 700, 950, 1200) if (x, y) not in ((450, 320), (950, 490)))
    out["hero-fleet"] = svg(1600, 900, f'''  <rect width="1600" height="900" fill="{d}"/>
  <g>{tiles}</g>
  <rect x="450" y="320" width="230" height="140" rx="12" fill="{li}"/><circle cx="565" cy="390" r="22" fill="{d}"/>
  <rect x="950" y="490" width="230" height="140" rx="12" fill="none" stroke="{li}" stroke-width="6"/>
''', "The fleet: a desk of agent tiles")

    bars = "".join(f'<rect x="{220 + i * 130}" y="{640 - h}" width="90" height="{h}" rx="6" fill="{m}"/>'
                   for i, h in enumerate((150, 210, 190, 290, 340, 420)))
    out["hero-powerbi"] = svg(1600, 900, f'''  <rect width="1600" height="900" fill="{d}"/>
  <g>{bars}</g>
  <path d="M180 660 H1060" stroke="{ln}" stroke-width="5"/>
  <circle cx="1240" cy="300" r="120" fill="none" stroke="{li}" stroke-width="16"/>
  <path d="M1185 300 l40 40 l75 -80" fill="none" stroke="{li}" stroke-width="16" stroke-linecap="round" stroke-linejoin="round"/>
''', "Power BI, shipped safely")

    out["hero-request"] = svg(1600, 900, f'''  <rect width="1600" height="900" fill="{d}"/>
  <path d="M230 470 C520 170, 820 760, 1290 380" fill="none" stroke="{ln}" stroke-width="6" stroke-dasharray="22 22"/>
  <circle cx="230" cy="470" r="56" fill="{m}"/><circle cx="700" cy="480" r="40" fill="{m}"/><circle cx="1000" cy="520" r="40" fill="{m}"/>
  <circle cx="1290" cy="380" r="80" fill="{li}"/>
  <path d="M1250 380 h80 M1300 345 l35 35 -35 35" stroke="{d}" stroke-width="14" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
''', "A request moving from question to answer")

    out["hero-release"] = svg(1600, 900, f'''  <rect width="1600" height="900" fill="{d}"/>
  <g>{dots(c, 120, 120, 6, 4, 70)}</g>
  <path d="M800 170 l70 185 185 70 -185 70 -70 185 -70 -185 -185 -70 185 -70 z" fill="{li}"/>
  <path d="M1180 560 l28 74 74 28 -74 28 -28 74 -28 -74 -74 -28 74 -28 z" fill="{m}"/>
  <path d="M1260 230 l18 46 46 18 -46 18 -18 46 -18 -46 -46 -18 46 -18 z" fill="{ln}"/>
''', "What is new")

    def title(name, motif, label):
        out[f"title-{name}"] = svg(1920, 460, f'  <rect width="1920" height="460" fill="{d}"/>\n{motif}', label)

    title("platform", f'''  <g fill="{m}"><rect x="1240" y="110" width="70" height="250" rx="8"/><rect x="1340" y="180" width="70" height="180" rx="8"/>
    <rect x="1440" y="70" width="70" height="290" rx="8"/><rect x="1540" y="220" width="70" height="140" rx="8"/><rect x="1640" y="140" width="70" height="220" rx="8"/></g>
  <path d="M1210 380 H1740" stroke="{ln}" stroke-width="4"/>
  <g fill="{li}"><circle cx="1275" cy="70" r="14"/><circle cx="1475" cy="34" r="16"/><circle cx="1675" cy="96" r="14"/></g>
''', "The platform")
    fleet_tiles = "".join(f'<rect x="{x}" y="{y}" width="160" height="96" rx="10" fill="{m}"/>'
                          for y in (60, 180, 300) for x in (1150, 1330, 1510, 1690) if (x, y) not in ((1330, 180), (1510, 300)))
    title("fleet", f'''  <g>{fleet_tiles}</g>
  <rect x="1330" y="180" width="160" height="96" rx="10" fill="{li}"/>
  <rect x="1510" y="300" width="160" height="96" rx="10" fill="none" stroke="{li}" stroke-width="4"/>
''', "The fleet")
    title("work-with-us", f'''  <path d="M1100 260 C1260 110, 1420 400, 1580 200 S1820 160, 1880 240" fill="none" stroke="{ln}" stroke-width="4" stroke-dasharray="14 14"/>
  <circle cx="1100" cy="260" r="26" fill="{m}"/><circle cx="1340" cy="250" r="18" fill="{m}"/><circle cx="1580" cy="200" r="18" fill="{m}"/>
  <circle cx="1760" cy="190" r="34" fill="{li}"/>
''', "Work with us")
    title("learn", f'''  <g fill="{m}"><rect x="1240" y="250" width="180" height="140" rx="8"/><rect x="1450" y="170" width="180" height="220" rx="8"/></g>
  <rect x="1660" y="80" width="180" height="310" rx="8" fill="{li}"/>
  <g fill="{d}"><circle cx="1330" cy="320" r="12"/><circle cx="1540" cy="280" r="12"/><circle cx="1750" cy="235" r="12"/></g>
''', "Learn")
    title("team", f'''  <g fill="{m}"><circle cx="1260" cy="240" r="84"/><circle cx="1430" cy="200" r="84"/><circle cx="1600" cy="250" r="84"/></g>
  <circle cx="1770" cy="210" r="84" fill="{li}"/>
''', "The team")
    title("impact", f'''  <path d="M1120 390 L1240 350 L1360 362 L1480 290 L1600 262 L1720 180 L1840 140" fill="none" stroke="{li}" stroke-width="8" stroke-linecap="round" stroke-linejoin="round"/>
  <g fill="{li}"><circle cx="1480" cy="290" r="12"/><circle cx="1720" cy="180" r="12"/><circle cx="1840" cy="140" r="16"/></g>
  <path d="M1100 410 H1880" stroke="{ln}" stroke-width="3"/>
''', "Impact")

    out["cta"] = svg(1200, 800, f'''  <rect width="1200" height="800" fill="{d}"/>
  <g>{dots(c, 80, 80, 16, 10, 70)}</g>
  <circle cx="900" cy="560" r="150" fill="{m}"/><circle cx="900" cy="560" r="70" fill="{li}"/>
''', "Office hours")

    steps = ("Submit", "Triage", "Plan", "Build", "Ship and|measure")
    boxes = ""
    for i, word in enumerate(steps):
        x = 40 + i * 312
        boxes += (f'  <rect x="{x}" y="60" width="280" height="240" rx="12" fill="#FFFFFF" stroke="{ln}" stroke-width="3"/>\n'
                  f'  <circle cx="{x + 56}" cy="128" r="32" fill="{c["accent"]}"/>\n'
                  f'  <text x="{x + 56}" y="140" text-anchor="middle" font-family="Segoe UI, Arial, sans-serif" font-size="32" font-weight="700" fill="#FFFFFF">{i + 1}</text>\n'
                  + "".join(f'  <text x="{x + 28}" y="{214 + n * 42}" font-family="Segoe UI, Arial, sans-serif" font-size="34" '
                            f'font-weight="600" fill="#242424">{part}</text>\n' for n, part in enumerate(word.split("|"))))
        if i < len(steps) - 1:
            boxes += f'  <path d="M{x + 284} 180 h24 m-10 -10 l10 10 -10 10" stroke="{c["accent"]}" stroke-width="4" fill="none"/>\n'
    out["request-flow"] = svg(1600, 360, f'  <rect width="1600" height="360" fill="{c["soft"]}"/>\n{boxes}',
                              "How a request moves: submit, triage, plan, build, ship and measure")
    return out


def size(svg_text: str) -> tuple[int, int]:
    m = re.search(r'width="(\d+)" height="(\d+)"', svg_text)
    return int(m.group(1)), int(m.group(2))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--accent", default=TEAL, help="the theme's primary colour, #RRGGBB")
    args = parser.parse_args(argv)
    if not re.fullmatch(r"#[0-9A-Fa-f]{6}", args.accent):
        parser.error("--accent is #RRGGBB")
    for name, text in art(args.accent).items():
        path = os.path.join(HERE, f"{name}.svg")
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        print(f"{os.path.relpath(path)}  {size(text)[0]}x{size(text)[1]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
