#!/usr/bin/env python3
"""Builds the static SVGs used by README.md: header, project cards, buttons, tech stack.

Edit the text in PROJECTS / HEADER below, then run:
    python3 scripts/static_assets.py
"""
import base64
import random
import textwrap
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"

# Monochrome: black background, white text, greys for accents
BG, BG_DARK, LINE = "#0a0a0a", "#000000", "#262626"
FG, FG_DIM, COMMENT = "#fafafa", "#d4d4d4", "#737373"
BLUE, CYAN, PURPLE = "#ffffff", "#d4d4d4", "#a3a3a3"
GREEN, ORANGE, RED, YELLOW = "#ffffff", "#8a8a8a", "#3f3f3f", "#5c5c5c"
MONO = "'JetBrains Mono','SFMono-Regular',Menlo,Consolas,'Liberation Mono',monospace"

HEADER = {
    "comment": "// hello, world",
    "name": "nurk3ldi",
    "role": "Full-stack developer · Astana, Kazakhstan",
    "prompt": "shipping web, mobile & AI products",
}

PROJECTS = [
    {
        "file": "project-airec.svg",
        "width": 1200,
        "name": "AIRec",
        "badge": ("open source", GREEN),
        "accent": BLUE,
        "text": "AI receptionist for small service businesses in Kazakhstan. "
        "Clients message the business's Telegram bot, the assistant answers from the "
        "real price list and opening hours, and files booking requests for the owner to confirm.",
        "stack": ["React 19", "Vite", "Tailwind v4", "FastAPI", "SQLAlchemy", "PostgreSQL", "Telegram"],
    },
    {
        "file": "project-valuai.svg",
        "width": 600,
        "name": "ValuAI",
        "badge": ("private · work", ORANGE),
        "accent": PURPLE,
        "text": "Platform for real-estate appraisers: valuation reports with PDF/DOCX export, "
        "market analogs search, teams, chats and an AI agent that fills reports.",
        "stack": ["React", "TypeScript", "Express", "Prisma", "Expo", "Docker"],
    },
    {
        "file": "project-skud.svg",
        "width": 600,
        "name": "SKUD",
        "badge": ("private · work", ORANGE),
        "accent": CYAN,
        "text": "Access control and visitor-pass system integrated with Hikvision (ISAPI) "
        "and Dahua devices, with background jobs and a web dashboard.",
        "stack": ["React", "TypeScript", "FastAPI", "PostgreSQL", "Redis", "Celery"],
    },
]


def header() -> str:
    w, h = 1200, 340
    avatar = base64.b64encode((ASSETS / "avatar.jpg").read_bytes()).decode()
    rnd = random.Random(7)
    stars = []
    for _ in range(46):
        x, y = rnd.randint(20, w - 20), rnd.randint(20, h - 20)
        if 70 < x < 330:  # keep the avatar area clean
            continue
        r = rnd.choice([0.8, 1.0, 1.2, 1.6])
        stars.append(
            f'<circle cx="{x}" cy="{y}" r="{r}" fill="{FG}" class="star" '
            f'style="animation-delay:{rnd.uniform(0, 4):.2f}s"/>'
        )
    cx, cy = 200, 180
    return f"""<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="nurk3ldi — full-stack developer">
  <style>
    .star {{ opacity:.15; animation: tw 4s ease-in-out infinite; }}
    @keyframes tw {{ 50% {{ opacity:.75; }} }}
    .ring {{ transform-origin:{cx}px {cy}px; animation: spin 14s linear infinite; }}
    @keyframes spin {{ to {{ transform: rotate(360deg); }} }}
    .cur {{ animation: blink 1.1s steps(1) infinite; }}
    @keyframes blink {{ 50% {{ opacity:0; }} }}
    @media (prefers-reduced-motion: reduce) {{ .star,.ring,.cur {{ animation:none; }} }}
  </style>
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{BG}"/><stop offset="1" stop-color="{BG_DARK}"/>
    </linearGradient>
    <linearGradient id="ring" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{BLUE}"/><stop offset=".5" stop-color="{PURPLE}"/><stop offset="1" stop-color="{CYAN}" stop-opacity="0"/>
    </linearGradient>
    <linearGradient id="name" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="{BLUE}"/><stop offset="1" stop-color="{PURPLE}"/>
    </linearGradient>
    <radialGradient id="glow1"><stop offset="0" stop-color="{BLUE}" stop-opacity=".09"/><stop offset="1" stop-color="{BLUE}" stop-opacity="0"/></radialGradient>
    <radialGradient id="glow2"><stop offset="0" stop-color="{PURPLE}" stop-opacity=".07"/><stop offset="1" stop-color="{PURPLE}" stop-opacity="0"/></radialGradient>
    <clipPath id="av"><circle cx="{cx}" cy="{cy}" r="104"/></clipPath>
    <clipPath id="card"><rect width="{w}" height="{h}" rx="18"/></clipPath>
  </defs>
  <g clip-path="url(#card)">
    <rect width="{w}" height="{h}" fill="url(#bg)"/>
    <circle cx="{cx}" cy="{cy}" r="260" fill="url(#glow1)"/>
    <circle cx="1060" cy="40" r="300" fill="url(#glow2)"/>
    {''.join(stars)}
    <circle cx="34" cy="30" r="6" fill="{RED}"/><circle cx="56" cy="30" r="6" fill="{YELLOW}"/><circle cx="78" cy="30" r="6" fill="{COMMENT}"/>
    <image x="{cx-104}" y="{cy-104}" width="208" height="208" clip-path="url(#av)" xlink:href="data:image/jpeg;base64,{avatar}" href="data:image/jpeg;base64,{avatar}"/>
    <circle class="ring" cx="{cx}" cy="{cy}" r="116" fill="none" stroke="url(#ring)" stroke-width="4" stroke-linecap="round" stroke-dasharray="520 210"/>
    <g font-family="{MONO}">
      <text x="372" y="108" font-size="21" fill="{COMMENT}">{escape(HEADER["comment"])}</text>
      <text x="368" y="180" font-size="72" font-weight="800" fill="url(#name)">{escape(HEADER["name"])}</text>
      <text x="372" y="228" font-size="25" fill="{FG}">{escape(HEADER["role"])}</text>
      <text x="372" y="280" font-size="22" fill="{FG_DIM}"><tspan fill="{GREEN}">❯ </tspan>{escape(HEADER["prompt"])}<tspan class="cur" fill="{BLUE}"> ▍</tspan></text>
    </g>
  </g>
  <rect x=".5" y=".5" width="{w-1}" height="{h-1}" rx="18" fill="none" stroke="{LINE}"/>
</svg>
"""


DESC, CHIP, CHIP_H, PAD = 20, 16, 34, 36


def layout(p: dict) -> tuple[list[str], list[list[tuple[str, float]]]]:
    w = p["width"]
    lines = textwrap.wrap(p["text"], int((w - 2 * PAD) / (DESC * 0.6)))
    rows, row, x = [], [], 0.0
    for s in p["stack"]:
        cw = len(s) * CHIP * 0.6 + 28
        if row and x + cw > w - 2 * PAD:
            rows.append(row)
            row, x = [], 0.0
        row.append((s, cw))
        x += cw + 10
    rows.append(row)
    return lines, rows


def card_height(p: dict) -> int:
    lines, rows = layout(p)
    return 118 + 30 * len(lines) + 22 + len(rows) * (CHIP_H + 10) + 22


def card(p: dict, h: int) -> str:
    w = p["width"]
    lines, rows = layout(p)
    badge_text, badge_color = p["badge"]
    bw = len(badge_text) * 15 * 0.6 + 30
    desc = "".join(
        f'<text x="{PAD}" y="{118 + i * 30}">{escape(line)}</text>' for i, line in enumerate(lines)
    )
    chips = []
    cy = h - 32 - len(rows) * (CHIP_H + 10) + 10
    for row in rows:
        x = PAD
        for s, cw in row:
            chips.append(
                f'<rect x="{x:.0f}" y="{cy}" width="{cw:.0f}" height="{CHIP_H}" rx="{CHIP_H // 2}" fill="{LINE}"/>'
                f'<text x="{x + cw / 2:.0f}" y="{cy + 23}" text-anchor="middle">{escape(s)}</text>'
            )
            x += cw + 10
        cy += CHIP_H + 10
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{escape(p["name"])}">
  <defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{BG}"/><stop offset="1" stop-color="{BG_DARK}"/></linearGradient></defs>
  <rect x=".5" y=".5" width="{w-1}" height="{h-1}" rx="18" fill="url(#bg)" stroke="{LINE}"/>
  <rect x="{PAD}" y="1" width="72" height="5" rx="2.5" fill="{p["accent"]}"/>
  <g font-family="{MONO}">
    <text x="{PAD}" y="68" font-size="36" font-weight="800" fill="{FG}"><tspan fill="{p["accent"]}">▸ </tspan>{escape(p["name"])}</text>
    <rect x="{w - PAD - bw:.0f}" y="36" width="{bw:.0f}" height="36" rx="18" fill="none" stroke="{badge_color}" stroke-width="1.5"/>
    <text x="{w - PAD - bw / 2:.0f}" y="59" font-size="15" text-anchor="middle" fill="{badge_color}">{escape(badge_text)}</text>
    <g font-size="{DESC}" fill="{FG_DIM}">{desc}</g>
    <g font-size="{CHIP}" fill="{BLUE}">{''.join(chips)}</g>
  </g>
</svg>
"""


ICONS = {
    # 24x24 line icons drawn in the accent colour
    "linkedin": '<rect x="2" y="2" width="20" height="20" rx="4" fill="{c}"/>'
    '<text x="12" y="17.5" font-size="13" font-weight="800" text-anchor="middle" fill="{bg}" '
    'font-family="Arial,Helvetica,sans-serif">in</text>',
    "instagram": '<rect x="3" y="3" width="18" height="18" rx="5" fill="none" stroke="{c}" stroke-width="2"/>'
    '<circle cx="12" cy="12" r="4.2" fill="none" stroke="{c}" stroke-width="2"/>'
    '<circle cx="17.2" cy="6.8" r="1.3" fill="{c}"/>',
    "web": '<circle cx="12" cy="12" r="9" fill="none" stroke="{c}" stroke-width="2"/>'
    '<ellipse cx="12" cy="12" rx="4" ry="9" fill="none" stroke="{c}" stroke-width="2"/>'
    '<path d="M3 12h18" stroke="{c}" stroke-width="2"/>',
}

BUTTONS = [
    ("btn-linkedin.svg", "linkedin", "LinkedIn", BLUE),
    ("btn-instagram.svg", "instagram", "Instagram", PURPLE),
    ("btn-website.svg", "web", "Website", CYAN),
]


def button(icon: str, label: str, color: str) -> str:
    w, h = 64 + len(label) * 18 * 0.6 + 26, 52
    glyph = ICONS[icon].format(c=color, bg=BG)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w:.0f}" height="{h}" viewBox="0 0 {w:.0f} {h}" role="img" aria-label="{label}">
  <rect x=".75" y=".75" width="{w - 1.5:.0f}" height="{h - 1.5}" rx="{h // 2}" fill="{BG}" stroke="{LINE}" stroke-width="1.5"/>
  <g transform="translate(22 14)">{glyph}</g>
  <text x="58" y="33" font-family="{MONO}" font-size="18" font-weight="700" fill="{FG}">{label}</text>
</svg>
"""


STACK = [
    ("frontend", [("react", "React"), ("typescript", "TypeScript"), ("javascript", "JavaScript"),
                  ("vite", "Vite"), ("tailwindcss", "Tailwind"), ("expo", "Expo"),
                  ("html5", "HTML"), ("css", "CSS")]),
    ("backend", [("python", "Python"), ("fastapi", "FastAPI"), ("sqlalchemy", "SQLAlchemy"),
                 ("nodedotjs", "Node.js"), ("express", "Express"), ("prisma", "Prisma"),
                 ("postgresql", "Postgres"), ("redis", "Redis")]),
    ("infra", [("docker", "Docker"), ("nginx", "Nginx"), ("linux", "Linux"), ("archlinux", "Arch"),
               ("hyprland", "Hyprland"), ("git", "Git"), ("github", "GitHub"), ("figma", "Figma")]),
]
ICON_CACHE = Path(__file__).with_name("icons.json")


def icon_paths() -> dict[str, str]:
    """Simple Icons path data, cached in scripts/icons.json (fetched once)."""
    import json
    import re
    import urllib.request

    cache = json.loads(ICON_CACHE.read_text()) if ICON_CACHE.exists() else {}
    for _, items in STACK:
        for slug, _ in items:
            if slug not in cache:
                req = urllib.request.Request(f"https://cdn.simpleicons.org/{slug}", headers={"User-Agent": "static-assets"})
                svg = urllib.request.urlopen(req, timeout=20).read().decode()
                cache[slug] = " ".join(re.findall(r' d="([^"]+)"', svg))
    ICON_CACHE.write_text(json.dumps(cache, indent=0, sort_keys=True))
    return cache


def stack_card() -> str:
    paths = icon_paths()
    w, row_h, top, label_w, cell = 1200, 128, 40, 190, 120
    h = top * 2 + row_h * len(STACK) - 24
    rows = []
    for r, (label, items) in enumerate(STACK):
        y = top + r * row_h
        rows.append(f'<text x="{PAD}" y="{y + 40}" font-size="20" font-weight="700" fill="{COMMENT}">{label}</text>')
        for i, (slug, name) in enumerate(items):
            cx = label_w + i * cell + cell / 2
            rows.append(
                f'<path transform="translate({cx - 22:.0f} {y + 6}) scale({44 / 24:.4f})" d="{paths[slug]}" fill="{FG}"/>'
                f'<text x="{cx:.0f}" y="{y + 82}" font-size="16" text-anchor="middle" fill="{FG_DIM}">{escape(name)}</text>'
            )
        if r:
            rows.append(f'<line x1="{PAD}" y1="{y - 22}" x2="{w - PAD}" y2="{y - 22}" stroke="{LINE}"/>')
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="Tech stack">
  <defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{BG}"/><stop offset="1" stop-color="{BG_DARK}"/></linearGradient></defs>
  <rect x=".5" y=".5" width="{w-1}" height="{h-1}" rx="18" fill="url(#bg)" stroke="{LINE}"/>
  <g font-family="{MONO}">{''.join(rows)}</g>
</svg>
"""


def main() -> None:
    (ASSETS / "header.svg").write_text(header())
    # cards of the same width sit side by side, so they share one height
    heights: dict[int, int] = {}
    for p in PROJECTS:
        heights[p["width"]] = max(heights.get(p["width"], 0), card_height(p))
    for p in PROJECTS:
        (ASSETS / p["file"]).write_text(card(p, heights[p["width"]]))
    (ASSETS / "stack.svg").write_text(stack_card())
    for file, icon, label, color in BUTTONS:
        (ASSETS / file).write_text(button(icon, label, color))
    print("written:", ", ".join(["header.svg"] + [p["file"] for p in PROJECTS] + ["stack.svg"] + [b[0] for b in BUTTONS]))


if __name__ == "__main__":
    main()
