#!/usr/bin/env python3
"""Builds the SVGs used by README.md: header, project cards, tech stack.

Edit the text in ABOUT / PROJECTS / HEADER / STACK below, then run:
    python3 scripts/static_assets.py                         # everything static into assets/
    python3 scripts/static_assets.py --views 123 --out /tmp/x   # view-count card preview
The workflow builds the view-count card (live number) into the `output` branch.
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
LINE_NO = "#3d3d3d"
MONO = "'JetBrains Mono','SFMono-Regular',Menlo,Consolas,'Liberation Mono',monospace"

HEADER = {
    "comment": "// hello, world",
    "name": "nurk3ldi",
    "role": "Full-stack developer · Astana, Kazakhstan",
    # these three lines take turns under the role, with a fade
    "prompts": [
        "building AI tools for real businesses",
        "turning ideas into products people use",
        "clean code · reliable systems · calm UX",
    ],
    "linkedin": "nurk3ldi",
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
        "stack": ["React 19", "Vite", "Tailwind v4", "FastAPI", "SQLAlchemy", "PostgreSQL"],
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


TYPE, HOLD, DELETE, GAP = 0.075, 2.2, 0.03, 0.5  # seconds: per typed char, pause, per deleted char, pause


def typewriter(lines: list[str], x: float, y: float, size: int = 22) -> tuple[str, str]:
    """Types each line char by char, holds it, deletes it, then the next one.

    Every character is its own <text> at a fixed x (monospace grid), so the caret
    lines up whatever font the viewer falls back to. Without CSS animation only
    the first line is shown.
    """
    cw = size * 0.6
    x0 = x + 2 * cw  # after the "❯ " prompt
    slots, t = [], 0.0
    for line in lines:
        typed = t + len(line) * TYPE
        held = typed + HOLD
        slots.append((t, held, line))
        t = held + len(line) * DELETE + GAP
    total = t

    def pct(sec: float) -> str:
        return f"{100 * sec / total:.3f}%"

    svg, css = [f'<text x="{x}" y="{y}" font-size="{size}" fill="{GREEN}">❯</text>'], []
    caret_frames = []
    for k, (start, held, line) in enumerate(slots):
        n = len(line)
        for i, ch in enumerate(line):
            on = start + (i + 1) * TYPE
            off = held + (n - i - 1) * DELETE
            if ch != " ":
                name = f"c{k}_{i}"
                css.append(f"@keyframes {name} {{ 0% {{ opacity:0 }} {pct(on)} {{ opacity:1 }} {pct(off)} {{ opacity:0 }} }}")
                svg.append(
                    f'<text x="{x0 + i * cw:.1f}" y="{y}" class="ch" '
                    f'style="animation-name:{name};opacity:{1 if k == 0 else 0}">{escape(ch)}</text>'
                )
        # caret: right after the last visible char
        for j in range(n + 1):
            caret_frames.append((start + j * TYPE, j))
        for j in range(n, -1, -1):
            caret_frames.append((held + (n - j) * DELETE, j))
    frames = " ".join(f"{pct(tm)} {{ transform:translateX({j * cw:.1f}px) }}" for tm, j in sorted(caret_frames))
    css.append(f"@keyframes caret {{ {frames} }}")
    first = len(lines[0]) * cw
    svg.append(
        f'<g class="caret" style="transform:translateX({first:.1f}px)">'
        f'<rect class="cur" x="{x0 + 1:.1f}" y="{y - size * 0.8:.1f}" width="{size * 0.5:.1f}" height="{size * 0.95:.1f}" fill="{BLUE}"/></g>'
    )
    css.insert(0, f".ch, .caret {{ animation-duration:{total:.2f}s; animation-iteration-count:infinite; animation-timing-function:steps(1, end); }}"
                  f" .caret {{ animation-name:caret; }}")
    group = f'<g font-size="{size}" fill="{FG_DIM}">{"".join(svg)}</g>'
    return group, "    " + "\n    ".join(css)


def link_card(icon: str, title: str, sub: str, arrow: bool = True, mobile: bool = False) -> str:
    """Small card under the header: icon, big title, grey subtitle (one per link).

    mobile: a taller card with everything centred and much bigger, because on a phone
    each of the three cards is only ~110 px wide.
    """
    if mobile:
        return link_card_mobile(icon, title, sub, arrow)
    w, h = 400, 120
    glyph = ICONS[icon].format(c=FG, bg=BG_DARK)
    hint = f'<text x="{w - 30}" y="44" font-size="22" text-anchor="end" fill="{COMMENT}">↗</text>' if arrow else ""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{escape(title)} — {escape(sub)}">
  <defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{BG}"/><stop offset="1" stop-color="{BG_DARK}"/></linearGradient></defs>
  <rect x=".5" y=".5" width="{w-1}" height="{h-1}" rx="8" fill="url(#bg)" stroke="{LINE}"/>
  <g transform="translate(30 {(h - 40) / 2:.0f}) scale({40 / 24:.4f})">{glyph}</g>
  <g font-family="{MONO}">
    <text x="94" y="57" font-size="28" font-weight="800" fill="{FG}">{escape(title)}</text>
    <text x="94" y="86" font-size="18" fill="{COMMENT}">{escape(sub)}</text>
    {hint}
  </g>
</svg>
"""


def link_card_mobile(icon: str, title: str, sub: str, arrow: bool) -> str:
    w, h = 240, 210
    glyph = ICONS[icon].format(c=FG, bg=BG_DARK)
    hint = f'<text x="{w - 18}" y="36" font-size="24" text-anchor="end" fill="{COMMENT}">↗</text>' if arrow else ""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{escape(title)} — {escape(sub)}">
  <defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{BG}"/><stop offset="1" stop-color="{BG_DARK}"/></linearGradient></defs>
  <rect x=".5" y=".5" width="{w-1}" height="{h-1}" rx="10" fill="url(#bg)" stroke="{LINE}"/>
  <g transform="translate({w / 2 - 28:.0f} 26) scale({56 / 24:.4f})">{glyph}</g>
  <g font-family="{MONO}" text-anchor="middle">
    <text x="{w / 2:.0f}" y="138" font-size="38" font-weight="800" fill="{FG}">{escape(title)}</text>
    <text x="{w / 2:.0f}" y="178" font-size="23" fill="{COMMENT}">{escape(sub)}</text>
  </g>
  {hint}
</svg>
"""


LINK_CARDS = [
    ("card-cv.svg", "cv", "CV", "resume · PDF"),
    ("card-linkedin.svg", "linkedin", "LinkedIn", "in/nurk3ldi"),
]


def header_mobile() -> str:
    w, h = 600, 520
    avatar = base64.b64encode((ASSETS / "avatar.jpg").read_bytes()).decode()
    rnd = random.Random(7)
    cx, cy, r = w // 2, 130, 90
    stars = []
    for _ in range(26):
        x, y = rnd.randint(16, w - 16), rnd.randint(16, h - 16)
        if abs(x - cx) < r + 30 and y < cy + r + 20:  # keep the avatar area clean
            continue
        stars.append(
            f'<circle cx="{x}" cy="{y}" r="{rnd.choice([0.8, 1.0, 1.2, 1.6])}" fill="{FG}" class="star" '
            f'style="animation-delay:{rnd.uniform(0, 4):.2f}s"/>'
        )
    size = 22
    widest = max(len(t) for t in HEADER["prompts"]) + 2
    prompts, typing_css = typewriter(HEADER["prompts"], x=round((w - widest * size * 0.6) / 2), y=462, size=size)
    role, place = (s.strip() for s in HEADER["role"].split("·"))
    return f"""<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="nurk3ldi — full-stack developer">
  <style>
    .star {{ opacity:.15; animation: tw 4s ease-in-out infinite; }}
    @keyframes tw {{ 50% {{ opacity:.75; }} }}
    .cur {{ animation: blink 1.1s steps(1) infinite; }}
    @keyframes blink {{ 50% {{ opacity:0; }} }}
{typing_css}
    @media (prefers-reduced-motion: reduce) {{ .star,.cur,.ch,.caret {{ animation:none; }} }}
  </style>
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{BG}"/><stop offset="1" stop-color="{BG_DARK}"/>
    </linearGradient>
    <linearGradient id="name" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="{BLUE}"/><stop offset="1" stop-color="{PURPLE}"/>
    </linearGradient>
    <radialGradient id="glow1"><stop offset="0" stop-color="{BLUE}" stop-opacity=".09"/><stop offset="1" stop-color="{BLUE}" stop-opacity="0"/></radialGradient>
    <clipPath id="av"><circle cx="{cx}" cy="{cy}" r="{r}"/></clipPath>
    <clipPath id="card"><rect width="{w}" height="{h}" rx="10"/></clipPath>
  </defs>
  <g clip-path="url(#card)">
    <rect width="{w}" height="{h}" fill="url(#bg)"/>
    <circle cx="{cx}" cy="{cy}" r="230" fill="url(#glow1)"/>
    {''.join(stars)}
    <image x="{cx-r}" y="{cy-r}" width="{2*r}" height="{2*r}" clip-path="url(#av)" xlink:href="data:image/jpeg;base64,{avatar}" href="data:image/jpeg;base64,{avatar}"/>
    <g font-family="{MONO}">
      <text x="{cx}" y="300" font-size="58" font-weight="800" text-anchor="middle" fill="url(#name)">{escape(HEADER["name"])}</text>
      <text x="{cx}" y="350" font-size="27" text-anchor="middle" fill="{FG}">{escape(role)}</text>
      <text x="{cx}" y="388" font-size="24" text-anchor="middle" fill="{COMMENT}">{escape(place)}</text>
      <line x1="{cx - 150}" y1="414" x2="{cx + 150}" y2="414" stroke="{LINE}"/>
      {prompts}
    </g>
  </g>
  <rect x=".5" y=".5" width="{w-1}" height="{h-1}" rx="10" fill="none" stroke="{LINE}"/>
</svg>
"""


def header() -> str:
    w, h = 1200, 300
    avatar = base64.b64encode((ASSETS / "avatar.jpg").read_bytes()).decode()
    rnd = random.Random(7)
    stars = []
    for _ in range(50):
        x, y = rnd.randint(20, w - 20), rnd.randint(20, h - 20)
        if 70 < x < 330:  # keep the avatar area clean
            continue
        r = rnd.choice([0.8, 1.0, 1.2, 1.6])
        stars.append(
            f'<circle cx="{x}" cy="{y}" r="{r}" fill="{FG}" class="star" '
            f'style="animation-delay:{rnd.uniform(0, 4):.2f}s"/>'
        )
    cx, cy = 200, h // 2
    prompts, typing_css = typewriter(HEADER["prompts"], x=372, y=222)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="nurk3ldi — full-stack developer">
  <style>
    .star {{ opacity:.15; animation: tw 4s ease-in-out infinite; }}
    @keyframes tw {{ 50% {{ opacity:.75; }} }}
    .cur {{ animation: blink 1.1s steps(1) infinite; }}
    @keyframes blink {{ 50% {{ opacity:0; }} }}
{typing_css}
    @media (prefers-reduced-motion: reduce) {{ .star,.cur,.ch,.caret {{ animation:none; }} }}
  </style>
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{BG}"/><stop offset="1" stop-color="{BG_DARK}"/>
    </linearGradient>
    <linearGradient id="name" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="{BLUE}"/><stop offset="1" stop-color="{PURPLE}"/>
    </linearGradient>
    <radialGradient id="glow1"><stop offset="0" stop-color="{BLUE}" stop-opacity=".09"/><stop offset="1" stop-color="{BLUE}" stop-opacity="0"/></radialGradient>
    <radialGradient id="glow2"><stop offset="0" stop-color="{PURPLE}" stop-opacity=".07"/><stop offset="1" stop-color="{PURPLE}" stop-opacity="0"/></radialGradient>
    <clipPath id="av"><circle cx="{cx}" cy="{cy}" r="110"/></clipPath>
    <clipPath id="card"><rect width="{w}" height="{h}" rx="8"/></clipPath>
  </defs>
  <g clip-path="url(#card)">
    <rect width="{w}" height="{h}" fill="url(#bg)"/>
    <circle cx="{cx}" cy="{cy}" r="260" fill="url(#glow1)"/>
    <circle cx="1060" cy="40" r="300" fill="url(#glow2)"/>
    {''.join(stars)}
    <image x="{cx-110}" y="{cy-110}" width="220" height="220" clip-path="url(#av)" xlink:href="data:image/jpeg;base64,{avatar}" href="data:image/jpeg;base64,{avatar}"/>
    <g font-family="{MONO}">
      <text x="372" y="78" font-size="20" fill="{COMMENT}">{escape(HEADER["comment"])}</text>
      <text x="370" y="134" font-size="52" font-weight="800" fill="url(#name)">{escape(HEADER["name"])}</text>
      <text x="372" y="178" font-size="25" fill="{FG}">{escape(HEADER["role"])}</text>
      {prompts}
    </g>
  </g>
  <rect x=".5" y=".5" width="{w-1}" height="{h-1}" rx="8" fill="none" stroke="{LINE}"/>
</svg>
"""


PAD = 36
# font sizes of a project card; MOBILE_CARD is for a 600-wide card shown full width on a phone
DESKTOP_CARD = {"desc": 20, "chip": 16, "chip_h": 34, "title": 36, "badge": 15, "lh": 30, "top": 118}
MOBILE_CARD = {"desc": 25, "chip": 21, "chip_h": 42, "title": 42, "badge": 19, "lh": 37, "top": 132}


def layout(p: dict, f: dict, w: int) -> tuple[list[str], list[list[tuple[str, float]]]]:
    lines = textwrap.wrap(p["text"], int((w - 2 * PAD) / (f["desc"] * 0.6)))
    rows, row, x = [], [], 0.0
    for s in p["stack"]:
        cw = len(s) * f["chip"] * 0.6 + 28
        if row and x + cw > w - 2 * PAD:
            rows.append(row)
            row, x = [], 0.0
        row.append((s, cw))
        x += cw + 10
    rows.append(row)
    return lines, rows


def card_height(p: dict, f: dict = DESKTOP_CARD, w: int | None = None) -> int:
    lines, rows = layout(p, f, w or p["width"])
    return f["top"] + f["lh"] * len(lines) + 22 + len(rows) * (f["chip_h"] + 10) + 22


def card(p: dict, h: int, f: dict = DESKTOP_CARD, w: int | None = None) -> str:
    w = w or p["width"]
    lines, rows = layout(p, f, w)
    badge_text, badge_color = p["badge"]
    bw = len(badge_text) * f["badge"] * 0.6 + 30
    bh = f["badge"] * 2.4
    desc = "".join(
        f'<text x="{PAD}" y="{f["top"] + i * f["lh"]}">{escape(line)}</text>' for i, line in enumerate(lines)
    )
    chips = []
    ch = f["chip_h"]
    cy = h - 32 - len(rows) * (ch + 10) + 10
    for row in rows:
        x = PAD
        for s, cw in row:
            chips.append(
                f'<rect x="{x:.0f}" y="{cy}" width="{cw:.0f}" height="{ch}" rx="5" fill="{LINE}"/>'
                f'<text x="{x + cw / 2:.0f}" y="{cy + ch / 2 + f["chip"] * 0.36:.0f}" text-anchor="middle">{escape(s)}</text>'
            )
            x += cw + 10
        cy += ch + 10
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{escape(p["name"])}">
  <defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{BG}"/><stop offset="1" stop-color="{BG_DARK}"/></linearGradient></defs>
  <rect x=".5" y=".5" width="{w-1}" height="{h-1}" rx="8" fill="url(#bg)" stroke="{LINE}"/>
  <rect x="{PAD}" y="1" width="72" height="5" rx="2.5" fill="{p["accent"]}"/>
  <g font-family="{MONO}">
    <text x="{PAD}" y="{32 + f["title"]}" font-size="{f["title"]}" font-weight="800" fill="{FG}">{escape(p["name"])}</text>
    <rect x="{w - PAD - bw:.0f}" y="{32 + f["title"] * 0.6 - bh / 2:.0f}" width="{bw:.0f}" height="{bh:.0f}" rx="5" fill="none" stroke="{badge_color}" stroke-width="1.5"/>
    <text x="{w - PAD - bw / 2:.0f}" y="{32 + f["title"] * 0.6 + f["badge"] * 0.36:.0f}" font-size="{f["badge"]}" text-anchor="middle" fill="{badge_color}">{escape(badge_text)}</text>
    <g font-size="{f["desc"]}" fill="{FG_DIM}">{desc}</g>
    <g font-size="{f["chip"]}" fill="{BLUE}">{''.join(chips)}</g>
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
    "cv": '<path d="M6 2.5h8.5L19 7v14.5H6z" fill="none" stroke="{c}" stroke-width="2" stroke-linejoin="round"/>'
    '<path d="M14 2.5V7h5M9.5 12.5h6M9.5 16.5h6" fill="none" stroke="{c}" stroke-width="2" stroke-linecap="round"/>',
    "eye": '<path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12z" fill="none" stroke="{c}" stroke-width="2" stroke-linejoin="round"/>'
    '<circle cx="12" cy="12" r="3.2" fill="{c}"/>',
    "web": '<circle cx="12" cy="12" r="9" fill="none" stroke="{c}" stroke-width="2"/>'
    '<ellipse cx="12" cy="12" rx="4" ry="9" fill="none" stroke="{c}" stroke-width="2"/>'
    '<path d="M3 12h18" stroke="{c}" stroke-width="2"/>',
}

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


PROMPT_COLOR = "#449dab"  # starship "bold cyan" in the user's foot theme (Tokyo Night regular6)


def terminal_stack(w: int = 1200, cols: int = 4, fs: int = 21, ifs: int = 19, isz: int = 24, row_h: int = 40) -> str:
    """Tech stack as a terminal session: `~ ❯ ls ~/stack/*` typed, then eza-style output.

    Plays once per page load. Without CSS animation everything is simply shown.
    """
    paths = icon_paths()
    cw = fs * 0.6
    x0, y = PAD, 66
    cmd = "ls ~/stack/*"
    out, css = [], [
        ".on {{ animation: on .01s steps(1, end) both; }}",
        ".blip {{ opacity:0; animation-name: blip; }}",
        "@keyframes blip {{ from, to {{ opacity:1 }} }}",
        "@keyframes on {{ from {{ opacity:0 }} to {{ opacity:1 }} }}",
        # Chrome stops the clock of an SVG <img> once no animation is running, so pending
        # (delayed) ones would never fire; this invisible infinite one keeps it ticking
        ".tick {{ animation: tick 1s linear infinite; }}",
        "@keyframes tick {{ to {{ transform: translateX(1px) }} }}",
        "@media (prefers-reduced-motion: reduce) {{ .on, .blip {{ animation:none; }} }}",
    ]

    def prompt(px: float, py: float) -> str:
        return (f'<text x="{px}" y="{py}" font-weight="700" fill="{PROMPT_COLOR}">~</text>'
                f'<text x="{px + 2 * cw:.1f}" y="{py}" font-weight="700" fill="{PROMPT_COLOR}">❯</text>')

    def caret(cx: float, cy: float) -> str:
        return f'<rect x="{cx:.1f}" y="{cy - fs * 0.82:.1f}" width="{cw:.1f}" height="{fs * 1.12:.1f}" fill="{FG}"'

    # 1. prompt + typed command (caret walks with the text)
    out.append(prompt(x0, y))
    t, step = 0.3, 0.035
    cmd_x = x0 + 4 * cw
    for i, ch in enumerate(cmd + " "):
        out.append(f'{caret(cmd_x + i * cw, y)} class="blip" style="animation-delay:{t:.3f}s;animation-duration:{step if i < len(cmd) else 0.2:.3f}s"/>')
        if i < len(cmd):
            t += step
            if ch != " ":
                out.append(f'<text x="{cmd_x + i * cw:.1f}" y="{y}" fill="{FG}" class="on" style="animation-delay:{t:.3f}s">{escape(ch)}</text>')
    t += 0.2  # "enter"

    # 2. output: one block per directory
    cell = (w - 2 * PAD) / cols
    y += 58
    for label, items in STACK:
        out.append(f'<text x="{x0}" y="{y}" fill="{FG}" font-weight="700" class="on" style="animation-delay:{t:.3f}s">/home/nurk3ldi/stack/{label}:</text>')
        t += 0.06
        y += 44
        for i, (slug, name) in enumerate(items):
            if i and i % cols == 0:
                y += row_h
            ix = x0 + (i % cols) * cell
            out.append(
                f'<g class="on" style="animation-delay:{t:.3f}s">'
                f'<path transform="translate({ix:.1f} {y - isz // 2 - round(ifs * 0.36)}) scale({isz / 24:.4f})" d="{paths[slug]}" fill="{FG}"/>'
                f'<text x="{ix + isz + 12:.1f}" y="{y}" font-size="{ifs}" fill="{FG_DIM}">{escape(name)}</text></g>'
            )
            t += 0.025
        t += 0.08
        y += 58

    # 3. fresh prompt with a solid block cursor (foot: style=block, blink=no)
    y -= 4
    out.append(f'<g class="on" style="animation-delay:{t:.3f}s">{prompt(x0, y)}{caret(x0 + 4 * cw, y)}/></g>')
    h = y + 40
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="Tech stack">
  <style>
    {chr(10).join("    " + c for c in css).strip().replace("{{", "{").replace("}}", "}")}
  </style>
  <defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{BG}"/><stop offset="1" stop-color="{BG_DARK}"/></linearGradient></defs>
  <rect x=".5" y=".5" width="{w-1}" height="{h-1}" rx="8" fill="url(#bg)" stroke="{LINE}"/>
  <rect class="tick" width="1" height="1" opacity="0"/>
  <g font-family="{MONO}" font-size="{fs}" xml:space="preserve">{"".join(out)}</g>
</svg>
"""


ABOUT = {
    "whoami": "nurk3ldi",
    "role": "full-stack developer",
    "based": "Astana, Kazakhstan",
    "email": "nurk3ldi@icloud.com",
    "now": [
        "building AIRec, an AI receptionist for small businesses",
        "shipping web + mobile platforms for clients at work",
    ],
    "studying": "AI/ML developer",
    "setup": ["Omarchy Linux", "Zed", "Claude Code"],
}


def json_lines(data: dict, inline_max: int = 50) -> list[str]:
    """Pretty JSON, short string lists kept on one line."""
    import json

    out = ["{"]
    items = list(data.items())
    for n, (k, v) in enumerate(items):
        comma = "," if n < len(items) - 1 else ""
        if isinstance(v, list) and len(json.dumps(v)) > inline_max:
            out.append(f'  "{k}": [')
            out += [f"    {json.dumps(x, ensure_ascii=False)}{',' if i < len(v) - 1 else ''}" for i, x in enumerate(v)]
            out.append(f"  ]{comma}")
        else:
            out.append(f'  "{k}": {json.dumps(v, ensure_ascii=False)}{comma}')
    out.append("}")
    return out


def about_card(mobile: bool = False) -> str:
    """`cat whois.json`. mobile: 600 wide, bigger font, long strings wrap onto
    continuation lines (no line number) so nothing is cut off."""
    import re

    if mobile:
        w, top, lh, fs, prompt_y, rule_y = 600, 118, 38, 24, 58, 82
        num_w, max_chars = 34, int((600 - PAD - 34 - 28 - 24) / (24 * 0.6))
        lines = json_lines(ABOUT, inline_max=24)
    else:
        w, top, lh, fs, prompt_y, rule_y = 1200, 104, 34, 21, 52, 72
        num_w, max_chars = 28, 10**6
        lines = json_lines(ABOUT)
    # (line number or None, text, part of a wrapped string)
    shown: list[tuple[int | None, str, bool]] = []
    for i, line in enumerate(lines):
        if len(line) <= max_chars:
            shown.append((i + 1, line, False))
            continue
        indent = len(line) - len(line.lstrip())
        parts = textwrap.wrap(line.strip(), max_chars - indent - 1)
        shown.append((i + 1, " " * indent + parts[0], True))
        shown += [(None, " " * (indent + 1) + part, True) for part in parts[1:]]
    h = top + lh * len(shown) + 12
    rows = []
    for i, (num, line, wrapped) in enumerate(shown):
        y = top + i * lh
        parts = []
        # "key": → bright, other strings → dim, punctuation → grey
        for tok in re.finditer(r'("(?:[^"\\]|\\.)*")(\s*:)?|([^"]+)', line):
            if tok.group(1) and tok.group(2):
                parts.append(f'<tspan fill="{FG}" font-weight="700">{escape(tok.group(1))}</tspan><tspan fill="{COMMENT}">:</tspan>')
            elif tok.group(1):
                parts.append(f'<tspan fill="{FG_DIM}">{escape(tok.group(1))}</tspan>')
            else:
                parts.append(f'<tspan fill="{COMMENT}">{escape(tok.group(3))}</tspan>')
        if wrapped:  # a string split over lines: all of it in the string colour
            parts = [f'<tspan fill="{FG_DIM}">{escape(line)}</tspan>']
        rows.append(
            (f'<text x="{PAD + num_w}" y="{y}" text-anchor="end" fill="{LINE_NO}">{num}</text>' if num else "")
            + f'<text x="{PAD + 2 * num_w}" y="{y}" xml:space="preserve">{"".join(parts)}</text>'
        )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="About: full-stack developer from Astana, nurk3ldi@icloud.com">
  <defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{BG}"/><stop offset="1" stop-color="{BG_DARK}"/></linearGradient></defs>
  <rect x=".5" y=".5" width="{w-1}" height="{h-1}" rx="8" fill="url(#bg)" stroke="{LINE}"/>
  <g font-family="{MONO}">
    <text x="{PAD}" y="{prompt_y}" font-size="{fs}" xml:space="preserve"><tspan fill="{PROMPT_COLOR}" font-weight="700">~ ❯</tspan><tspan fill="{FG}"> cat </tspan><tspan fill="{FG}" font-weight="700">whois.json</tspan></text>
    <line x1="{PAD}" y1="{rule_y}" x2="{w - PAD}" y2="{rule_y}" stroke="{LINE}"/>
    <g font-size="{fs}">{"".join(rows)}</g>
  </g>
</svg>
"""


def combine(svgs: list[str], vertical: bool, gap: int = 24, label: str = "") -> str:
    """Puts standalone card SVGs into one image, side by side or stacked.

    Cards that sat next to each other as two 49 % images can then be swapped for a
    stacked version on a phone (an <img width> can't change with the screen size).
    """
    import re

    sizes = [tuple(int(v) for v in re.search(r'width="(\d+)" height="(\d+)"', s).groups()) for s in svgs]
    if vertical:
        w, h = max(sw for sw, _ in sizes), sum(sh for _, sh in sizes) + gap * (len(svgs) - 1)
    else:
        w, h = sum(sw for sw, _ in sizes) + gap * (len(svgs) - 1), max(sh for _, sh in sizes)
    parts, pos = [], 0
    for s, (sw, sh) in zip(svgs, sizes):
        x, y = (0, pos) if vertical else (pos, 0)
        parts.append(re.sub(r'<svg xmlns="http://www.w3.org/2000/svg"( xmlns:xlink="[^"]*")?', f'<svg x="{x}" y="{y}"', s, count=1))
        pos += (sh if vertical else sw) + gap
    return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{w}" height="{h}" '
            f'viewBox="0 0 {w} {h}" role="img" aria-label="{escape(label)}">\n' + "".join(parts) + "</svg>\n")


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--views", type=int, help="only build card-views.svg with this count (used by the workflow)")
    ap.add_argument("--out", default=str(ASSETS))
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    if args.views is not None:
        # the live view count changes, so the workflow builds this card into the output branch
        views = f"{args.views:,}"
        (out / "card-views.svg").write_text(link_card("eye", views, "profile views", arrow=False))
        (out / "card-views-mobile.svg").write_text(link_card("eye", views, "profile views", arrow=False, mobile=True))
        print(f"written: {out}/card-views.svg, {out}/card-views-mobile.svg")
        return
    # every asset has a `-mobile` twin that README.md swaps in on narrow screens (<picture>)
    files = {
        "header.svg": header(),
        "header-mobile.svg": header_mobile(),
        "stack.svg": terminal_stack(),
        "stack-mobile.svg": terminal_stack(w=600, cols=2, fs=24, ifs=24, isz=28, row_h=46),
        "about.svg": about_card(),
        "about-mobile.svg": about_card(mobile=True),
    }
    # cards of the same width sit side by side, so they share one height
    heights: dict[int, int] = {}
    for p in PROJECTS:
        heights[p["width"]] = max(heights.get(p["width"], 0), card_height(p))
    work, work_mobile = [], []
    for p in PROJECTS:
        desktop = card(p, heights[p["width"]])
        mobile = card(p, card_height(p, MOBILE_CARD, 600), MOBILE_CARD, 600)
        if p["width"] == 1200:
            files[p["file"]] = desktop
            files[p["file"].replace(".svg", "-mobile.svg")] = mobile
        else:
            work.append(desktop)
            work_mobile.append(mobile)
    files["projects-work.svg"] = combine(work, vertical=False, label="ValuAI and SKUD (private work projects)")
    files["projects-work-mobile.svg"] = combine(work_mobile, vertical=True, label="ValuAI and SKUD (private work projects)")
    for file, icon, title, sub in LINK_CARDS:
        files[file] = link_card(icon, title, sub)
        files[file.replace(".svg", "-mobile.svg")] = link_card(icon, title, sub, mobile=True)
    for name, svg in files.items():
        (out / name).write_text(svg)
    print("written:", ", ".join(files))


if __name__ == "__main__":
    main()
