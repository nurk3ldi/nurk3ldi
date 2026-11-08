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


def link_card(icon: str, title: str, sub: str, arrow: bool = True) -> str:
    """Small card under the header: icon, big title, grey subtitle (one per link)."""
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


LINK_CARDS = [
    ("card-cv.svg", "cv", "CV", "resume · PDF"),
    ("card-linkedin.svg", "linkedin", "LinkedIn", "in/nurk3ldi"),
]


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
                f'<rect x="{x:.0f}" y="{cy}" width="{cw:.0f}" height="{CHIP_H}" rx="5" fill="{LINE}"/>'
                f'<text x="{x + cw / 2:.0f}" y="{cy + 23}" text-anchor="middle">{escape(s)}</text>'
            )
            x += cw + 10
        cy += CHIP_H + 10
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{escape(p["name"])}">
  <defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{BG}"/><stop offset="1" stop-color="{BG_DARK}"/></linearGradient></defs>
  <rect x=".5" y=".5" width="{w-1}" height="{h-1}" rx="8" fill="url(#bg)" stroke="{LINE}"/>
  <rect x="{PAD}" y="1" width="72" height="5" rx="2.5" fill="{p["accent"]}"/>
  <g font-family="{MONO}">
    <text x="{PAD}" y="68" font-size="36" font-weight="800" fill="{FG}">{escape(p["name"])}</text>
    <rect x="{w - PAD - bw:.0f}" y="36" width="{bw:.0f}" height="36" rx="5" fill="none" stroke="{badge_color}" stroke-width="1.5"/>
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


def terminal_stack() -> str:
    """Tech stack as a terminal session: `~ ❯ ls ~/stack/*` typed, then eza-style output.

    Plays once per page load. Without CSS animation everything is simply shown.
    """
    paths = icon_paths()
    w, fs, cw = 1200, 21, 21 * 0.6
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
    cols, isz, ifs = 4, 24, 19
    cell = (w - 2 * PAD) / cols
    y += 58
    for label, items in STACK:
        out.append(f'<text x="{x0}" y="{y}" fill="{FG}" font-weight="700" class="on" style="animation-delay:{t:.3f}s">/home/nurk3ldi/stack/{label}:</text>')
        t += 0.06
        y += 44
        for i, (slug, name) in enumerate(items):
            if i and i % cols == 0:
                y += 40
            ix = x0 + (i % cols) * cell
            out.append(
                f'<g class="on" style="animation-delay:{t:.3f}s">'
                f'<path transform="translate({ix:.1f} {y - 19}) scale({isz / 24:.4f})" d="{paths[slug]}" fill="{FG}"/>'
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


def json_lines(data: dict) -> list[str]:
    """Pretty JSON, short string lists kept on one line."""
    import json

    out = ["{"]
    items = list(data.items())
    for n, (k, v) in enumerate(items):
        comma = "," if n < len(items) - 1 else ""
        if isinstance(v, list) and len(json.dumps(v)) > 50:
            out.append(f'  "{k}": [')
            out += [f"    {json.dumps(x, ensure_ascii=False)}{',' if i < len(v) - 1 else ''}" for i, x in enumerate(v)]
            out.append(f"  ]{comma}")
        else:
            out.append(f'  "{k}": {json.dumps(v, ensure_ascii=False)}{comma}')
    out.append("}")
    return out


def about_card() -> str:
    import re

    lines = json_lines(ABOUT)
    w, top, lh = 1200, 104, 34
    h = top + lh * len(lines) + 12
    rows = []
    for i, line in enumerate(lines):
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
        rows.append(
            f'<text x="{PAD + 28}" y="{y}" text-anchor="end" fill="{LINE_NO}">{i + 1}</text>'
            f'<text x="{PAD + 56}" y="{y}" xml:space="preserve">{"".join(parts)}</text>'
        )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="About: full-stack developer from Astana, nurk3ldi@icloud.com">
  <defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{BG}"/><stop offset="1" stop-color="{BG_DARK}"/></linearGradient></defs>
  <rect x=".5" y=".5" width="{w-1}" height="{h-1}" rx="8" fill="url(#bg)" stroke="{LINE}"/>
  <g font-family="{MONO}">
    <text x="{PAD}" y="52" font-size="21" xml:space="preserve"><tspan fill="{PROMPT_COLOR}" font-weight="700">~ ❯</tspan><tspan fill="{FG}"> cat </tspan><tspan fill="{FG}" font-weight="700">whois.json</tspan></text>
    <line x1="{PAD}" y1="72" x2="{w - PAD}" y2="72" stroke="{LINE}"/>
    <g font-size="21">{"".join(rows)}</g>
  </g>
</svg>
"""


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
        (out / "card-views.svg").write_text(link_card("eye", f"{args.views:,}", "profile views", arrow=False))
        print(f"written: {out}/card-views.svg")
        return
    written = ["header.svg"]
    (out / "header.svg").write_text(header())
    # cards of the same width sit side by side, so they share one height
    heights: dict[int, int] = {}
    for p in PROJECTS:
        heights[p["width"]] = max(heights.get(p["width"], 0), card_height(p))
    for p in PROJECTS:
        (out / p["file"]).write_text(card(p, heights[p["width"]]))
        written.append(p["file"])
    (out / "stack.svg").write_text(terminal_stack())
    (out / "about.svg").write_text(about_card())
    for file, icon, title, sub in LINK_CARDS:
        (out / file).write_text(link_card(icon, title, sub))
        written.append(file)
    print("written:", ", ".join(written + ["stack.svg", "about.svg"]))


if __name__ == "__main__":
    main()
