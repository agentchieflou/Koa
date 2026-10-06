#!/usr/bin/env python3
"""Draw the site's logo and artwork as SVG, in one theme colour (site/README.md, step 1). Stdlib only.

    python site/assets/make_assets.py                    the Teal theme, #03787C
    python site/assets/make_assets.py --accent "#498205"  any other theme's primary colour

Every image is geometry in shades of the accent (deep, mid, light, line) with no text, so it stays true when the
copy changes and never needs translating; the one exception is `request-flow`, whose words are also its alt text in
`site/pages/get-help.md`. SharePoint takes PNG for the logo, hero tiles and title areas: render each SVG at its
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

    help_path = (f'  <path d="M230 470 C520 170, 820 760, 1290 380" fill="none" stroke="{ln}" stroke-width="6" stroke-dasharray="22 22"/>\n'
                 f'  <circle cx="230" cy="470" r="56" fill="{m}"/><circle cx="700" cy="480" r="40" fill="{m}"/><circle cx="1000" cy="520" r="40" fill="{m}"/>\n'
                 f'  <circle cx="1290" cy="380" r="80" fill="{li}"/>\n'
                 f'  <path d="M1250 380 l26 26 52 -56" stroke="{d}" stroke-width="14" fill="none" stroke-linecap="round" stroke-linejoin="round"/>\n')
    out["hero-help"] = svg(1600, 900, f'  <rect width="1600" height="900" fill="{d}"/>\n' + help_path, "A request moving to done")

    cells = "".join(f'<rect x="{180 + i * 150}" y="{200 + j * 90}" width="138" height="78" rx="6" fill="{li if (i, j) in ((2, 1), (4, 2)) else m}"/>'
                    for j in range(4) for i in range(5))
    out["hero-reports"] = svg(1600, 900, f'''  <rect width="1600" height="900" fill="{d}"/>
  <g>{cells}</g>
  <path d="M1000 560 L1110 500 L1220 520 L1330 400 L1440 330" fill="none" stroke="{li}" stroke-width="10" stroke-linecap="round" stroke-linejoin="round"/>
  <g fill="{li}"><circle cx="1330" cy="400" r="14"/><circle cx="1440" cy="330" r="18"/></g>
''', "A usage report")

    out["hero-contact"] = svg(1600, 900, f'''  <rect width="1600" height="900" fill="{d}"/>
  <g fill="{m}"><circle cx="520" cy="420" r="130"/><circle cx="760" cy="380" r="130"/></g>
  <circle cx="1000" cy="430" r="130" fill="{li}"/>
  <path d="M1120 220 h260 a30 30 0 0 1 30 30 v130 a30 30 0 0 1 -30 30 h-170 l-60 50 v-50 h-30 a30 30 0 0 1 -30 -30 v-130 a30 30 0 0 1 30 -30 z" fill="none" stroke="{ln}" stroke-width="8"/>
  <g fill="{ln}"><circle cx="1190" cy="315" r="12"/><circle cx="1250" cy="315" r="12"/><circle cx="1310" cy="315" r="12"/></g>
''', "The team")

    spark = (f'  <path d="M800 170 l70 185 185 70 -185 70 -70 185 -70 -185 -185 -70 185 -70 z" fill="{li}"/>\n'
             f'  <path d="M1180 560 l28 74 74 28 -74 28 -28 74 -28 -74 -74 -28 74 -28 z" fill="{m}"/>\n'
             f'  <path d="M1260 230 l18 46 46 18 -46 18 -18 46 -18 -46 -46 -18 46 -18 z" fill="{ln}"/>\n')
    out["hero-copilot"] = svg(1600, 900, f'  <rect width="1600" height="900" fill="{d}"/>\n  <g>{dots(c, 120, 120, 6, 4, 70)}</g>\n' + spark,
                              "Data Czars in Copilot")

    def title(name, motif, label):
        out[f"title-{name}"] = svg(1920, 460, f'  <rect width="1920" height="460" fill="{d}"/>\n{motif}', label)

    title("start", f'''  <g fill="{m}"><rect x="1200" y="300" width="120" height="60" rx="8"/><rect x="1340" y="240" width="120" height="120" rx="8"/>
    <rect x="1480" y="180" width="120" height="180" rx="8"/></g>
  <rect x="1620" y="120" width="120" height="240" rx="8" fill="{li}"/>
  <path d="M1650 196 l26 22 -26 22 M1690 244 h28" stroke="{d}" stroke-width="10" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
  <path d="M1170 380 H1770" stroke="{ln}" stroke-width="4"/>
''', "Steps up to a notebook")
    title("products", f'''  <g fill="{m}"><rect x="1240" y="110" width="70" height="250" rx="8"/><rect x="1340" y="180" width="70" height="180" rx="8"/>
    <rect x="1440" y="70" width="70" height="290" rx="8"/><rect x="1540" y="220" width="70" height="140" rx="8"/><rect x="1640" y="140" width="70" height="220" rx="8"/></g>
  <path d="M1210 380 H1740" stroke="{ln}" stroke-width="4"/>
  <g fill="{li}"><circle cx="1275" cy="70" r="14"/><circle cx="1475" cy="34" r="16"/><circle cx="1675" cy="96" r="14"/></g>
''', "Products")
    grid = "".join(f'<rect x="{1180 + i * 110}" y="{90 + j * 70}" width="100" height="60" rx="5" fill="{li if (i, j) == (3, 2) else m}"/>'
                   for j in range(4) for i in range(6))
    title("reports", f'  <g>{grid}</g>\n', "Usage reports")
    title("help", f'''  <path d="M1100 260 C1260 110, 1420 400, 1580 200 S1820 160, 1880 240" fill="none" stroke="{ln}" stroke-width="4" stroke-dasharray="14 14"/>
  <circle cx="1100" cy="260" r="26" fill="{m}"/><circle cx="1340" cy="250" r="18" fill="{m}"/><circle cx="1580" cy="200" r="18" fill="{m}"/>
  <circle cx="1760" cy="190" r="34" fill="{li}"/>
''', "Get help")
    title("links", f'''  <g fill="none" stroke="{m}" stroke-width="18"><rect x="1180" y="170" width="220" height="120" rx="60"/><rect x="1500" y="170" width="220" height="120" rx="60"/></g>
  <rect x="1340" y="170" width="220" height="120" rx="60" fill="none" stroke="{li}" stroke-width="18"/>
''', "Links")
    title("contact", f'''  <g fill="{m}"><circle cx="1260" cy="240" r="84"/><circle cx="1430" cy="200" r="84"/><circle cx="1600" cy="250" r="84"/></g>
  <circle cx="1770" cy="210" r="84" fill="{li}"/>
''', "Contact")
    fleet_tiles = "".join(f'<rect x="{x}" y="{y}" width="160" height="96" rx="10" fill="{m}"/>'
                          for y in (60, 180, 300) for x in (1150, 1330, 1510, 1690) if (x, y) not in ((1330, 180), (1510, 300)))
    title("fleet", f'''  <g>{fleet_tiles}</g>
  <rect x="1330" y="180" width="160" height="96" rx="10" fill="{li}"/>
  <rect x="1510" y="300" width="160" height="96" rx="10" fill="none" stroke="{li}" stroke-width="4"/>
''', "The fleet")
    title("copilot", f'''  <path d="M1500 60 l52 138 138 52 -138 52 -52 138 -52 -138 -138 -52 138 -52 z" fill="{li}"/>
  <path d="M1760 260 l22 58 58 22 -58 22 -22 58 -22 -58 -58 -22 58 -22 z" fill="{m}"/>
  <path d="M1270 120 l14 36 36 14 -36 14 -14 36 -14 -36 -36 -14 36 -14 z" fill="{ln}"/>
''', "Copilot")

    out["cta"] = svg(1200, 800, f'''  <rect width="1200" height="800" fill="{d}"/>
  <g>{dots(c, 80, 80, 16, 10, 70)}</g>
  <circle cx="900" cy="560" r="150" fill="{m}"/><circle cx="900" cy="560" r="70" fill="{li}"/>
''', "Office hours")

    steps = ("Submit", "Jira ticket", "Triage", "Work", "Done")
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
                              "What happens next: submit, Jira ticket, triage, work, done")
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
