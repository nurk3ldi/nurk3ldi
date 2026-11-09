#!/usr/bin/env python3
"""Draws stats.svg, streak.svg and life.svg (black and white) from the GitHub GraphQL API.

Runs in the `profile` workflow with GITHUB_TOKEN. Local test without a token:
    python3 .github/scripts/stats.py --mock mock.json --out dist
"""
import argparse
import json
import os
import urllib.request
from datetime import date, timedelta
from pathlib import Path
from xml.sax.saxutils import escape

USER = os.environ.get("PROFILE_USER", "nurk3ldi")

BG, BG_DARK, LINE = "#0a0a0a", "#000000", "#262626"
FG, FG_DIM, COMMENT = "#fafafa", "#d4d4d4", "#737373"
BLUE = CYAN = PURPLE = GREEN = ORANGE = YELLOW = FG
MONO = "'JetBrains Mono','SFMono-Regular',Menlo,Consolas,'Liberation Mono',monospace"
# segments of the language bar, brightest first
SHADES = ["#fafafa", "#a3a3a3", "#6b6b6b", "#474747", "#333333"]
IGNORED_LANGS = {"Mako"}

QUERY = """
query($login: String!) {
  user(login: $login) {
    followers { totalCount }
    pullRequests { totalCount }
    repositories(ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC, first: 100) {
      totalCount
      nodes {
        stargazerCount
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name color } }
        }
      }
    }
    contributionsCollection {
      totalCommitContributions
      restrictedContributionsCount
      contributionCalendar {
        totalContributions
        weeks { contributionDays { contributionCount date } }
      }
    }
  }
}
"""


def fetch() -> dict:
    token = os.environ["GITHUB_TOKEN"]
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": USER}}).encode(),
        headers={"Authorization": f"bearer {token}", "User-Agent": "profile-stats"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        body = json.load(r)
    if "errors" in body:
        raise SystemExit(f"GraphQL errors: {body['errors']}")
    return body["data"]["user"]


def streak_info(days: list[dict]) -> dict:
    """Runs of consecutive days with at least one contribution."""
    counts = {date.fromisoformat(d["date"]): d["contributionCount"] for d in days}
    ordered = sorted(counts)
    runs, start = [], None
    for d in ordered:
        if counts[d] and start is None:
            start = d
        if not counts[d] and start is not None:
            runs.append((start, d - timedelta(days=1)))
            start = None
    if start is not None:
        runs.append((start, ordered[-1]))
    length = lambda r: (r[1] - r[0]).days + 1
    today = ordered[-1]
    current = next((r for r in reversed(runs) if r[1] >= today - timedelta(days=1)), None)
    longest = max(runs, key=lambda r: (length(r), r[1]), default=None)
    best = max(ordered, key=lambda d: (counts[d], d))
    return {
        "current": current, "current_len": length(current) if current else 0,
        "longest": longest, "longest_len": length(longest) if longest else 0,
        "first": runs[0][0] if runs else None,
        "active": sum(1 for d in ordered if counts[d]),
        "best": best, "best_count": counts[best],
    }


def fmt(d: date) -> str:
    return f"{d:%b} {d.day}"


def span(r) -> str:
    if not r:
        return "—"
    return fmt(r[0]) if r[0] == r[1] else f"{fmt(r[0])} – {fmt(r[1])}"


def pct(v: float) -> str:
    return f"{v:.0f}%" if v >= 10 else f"{v:.1f}%"


def frame(w: int, h: int, title: str, body: str, tsize: int = 21, ty: int = 50) -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{escape(title)}">
  <defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{BG}"/><stop offset="1" stop-color="{BG_DARK}"/></linearGradient></defs>
  <rect x=".5" y=".5" width="{w-1}" height="{h-1}" rx="8" fill="url(#bg)" stroke="{LINE}"/>
  <g font-family="{MONO}">
    <text x="32" y="{ty}" font-size="{tsize}" font-weight="700" fill="{FG}"><tspan fill="{BLUE}">❯ </tspan>{escape(title)}</text>
{body}
  </g>
</svg>
"""


def stats_svg(u: dict, mobile: bool = False) -> str:
    cc = u["contributionsCollection"]
    cal = cc["contributionCalendar"]
    days = [d for wk in cal["weeks"] for d in wk["contributionDays"]]
    info = streak_info(days)
    repos = u["repositories"]
    stars = sum(n["stargazerCount"] for n in repos["nodes"])
    items = [
        ("contributions", cal["totalContributions"], BLUE),
        ("commits", cc["totalCommitContributions"] + cc["restrictedContributionsCount"], PURPLE),
        ("pull requests", u["pullRequests"]["totalCount"], CYAN),
        ("public repos", repos["totalCount"], GREEN),
        ("stars", stars, YELLOW),
        ("followers", u["followers"]["totalCount"], ORANGE),
    ]
    body = []
    if mobile:
        for i, (label, value, color) in enumerate(items):
            x, y = 36 + (i % 2) * 282, 136 + (i // 2) * 106
            body.append(
                f'    <text x="{x}" y="{y}" font-size="48" font-weight="800" fill="{color}">{value:,}</text>\n'
                f'    <text x="{x}" y="{y + 34}" font-size="23" fill="{COMMENT}">{label}</text>'
            )
        y = 136 + 3 * 106 - 12
        body.append(f'    <line x1="32" y1="{y}" x2="568" y2="{y}" stroke="{LINE}"/>')
        body.append(
            f'    <text x="36" y="{y + 50}" font-size="23" fill="{FG_DIM}">active days '
            f'<tspan fill="{FG}" font-weight="700">{info["active"]}</tspan>'
            f'<tspan fill="{COMMENT}">  ·  12 mo</tspan></text>'
        )
        body.append(
            f'    <text x="36" y="{y + 88}" font-size="23" fill="{FG_DIM}">best day '
            f'<tspan fill="{FG}" font-weight="700">{info["best_count"]}</tspan>'
            f'<tspan fill="{COMMENT}"> on {fmt(info["best"])}</tspan></text>'
        )
        return frame(600, y + 120, "github activity", "\n".join(body), tsize=26, ty=58)
    for i, (label, value, color) in enumerate(items):
        x, y = 32 + (i % 3) * 182, 110 + (i // 3) * 78
        body.append(
            f'    <text x="{x}" y="{y}" font-size="36" font-weight="800" fill="{color}">{value:,}</text>\n'
            f'    <text x="{x}" y="{y + 26}" font-size="16" fill="{COMMENT}">{label}</text>'
        )
    y = 266
    body.append(f'    <line x1="32" y1="{y - 22}" x2="568" y2="{y - 22}" stroke="{LINE}"/>')
    body.append(
        f'    <text x="32" y="{y + 6}" font-size="17" fill="{FG_DIM}">active days '
        f'<tspan fill="{FG}" font-weight="700">{info["active"]}</tspan>'
        f'<tspan fill="{COMMENT}">  ·  </tspan>best day '
        f'<tspan fill="{FG}" font-weight="700">{info["best_count"]}</tspan>'
        f'<tspan fill="{COMMENT}"> on {fmt(info["best"])}  ·  12 mo</tspan></text>'
    )
    return frame(600, 300, "github activity", "\n".join(body))


FLAME = ("M12 2.5c.6 2.6 2.4 4.2 3.8 5.9 1.4 1.7 2.2 3.4 2.2 5.4a6 6 0 0 1-12 0c0-2.3 1.1-4 2.4-5.3"
         ".2 1.6.9 2.8 2.1 3.4-.4-3.2.3-6.4 1.5-9.4z")


def streak_svg(u: dict, mobile: bool = False) -> str:
    cal = u["contributionsCollection"]["contributionCalendar"]
    days = [d for wk in cal["weeks"] for d in wk["contributionDays"]]
    info = streak_info(days)
    cx, cy, r = (300, 200, 74) if mobile else (300, 150, 58)
    circ = 2 * 3.14159 * r
    # the ring fills to current / longest streak
    filled = info["current_len"] / info["longest_len"] if info["longest_len"] else 0
    offset = circ * (1 - filled)
    since = f"since {fmt(info['first'])}, {info['first'].year}" if info["first"] else "last 12 months"
    cur = info["current"]
    cur_span = (f"{fmt(cur[0])} – today" if cur and cur[0] != cur[1] else "today") if cur else "start one today"

    if mobile:
        def col(x: int, value: int, label: str, sub: str) -> str:
            return (f'    <text x="{x}" y="470" font-size="46" font-weight="800" text-anchor="middle" fill="{FG}">{value:,}</text>\n'
                    f'    <text x="{x}" y="510" font-size="23" text-anchor="middle" fill="{FG_DIM}">{label}</text>\n'
                    f'    <text x="{x}" y="544" font-size="20" text-anchor="middle" fill="{COMMENT}">{escape(sub)}</text>')

        body = [
            f'    <style>.ring {{ animation: draw 1.2s ease-out both; }} @keyframes draw {{ from {{ stroke-dashoffset:{circ:.1f}; }} }}'
            f' @media (prefers-reduced-motion: reduce) {{ .ring {{ animation:none; }} }}</style>',
            f'    <circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{LINE}" stroke-width="8"/>',
            f'    <circle class="ring" cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{FG}" stroke-width="8" stroke-linecap="round"'
            f' stroke-dasharray="{circ:.1f}" stroke-dashoffset="{offset:.1f}" style="stroke-dashoffset:{offset:.1f}" transform="rotate(-90 {cx} {cy})"/>',
            f'    <circle cx="{cx}" cy="{cy - r}" r="22" fill="{BG}"/>',
            f'    <path transform="translate({cx - 16} {cy - r - 17}) scale(1.3333)" d="{FLAME}" fill="{FG}"/>',
            f'    <text x="{cx}" y="{cy + 18}" font-size="52" font-weight="800" text-anchor="middle" fill="{FG}">{info["current_len"]}</text>',
            f'    <text x="{cx}" y="{cy + r + 48}" font-size="24" font-weight="700" text-anchor="middle" fill="{FG}">current streak</text>',
            f'    <text x="{cx}" y="{cy + r + 80}" font-size="20" text-anchor="middle" fill="{COMMENT}">{escape(cur_span)}</text>',
            f'    <line x1="32" y1="392" x2="568" y2="392" stroke="{LINE}"/><line x1="300" y1="416" x2="300" y2="552" stroke="{LINE}"/>',
            col(160, cal["totalContributions"], "contributions", since),
            col(440, info["longest_len"], "longest streak", span(info["longest"])),
        ]
        return frame(600, 586, "commit streak", "\n".join(body), tsize=26, ty=58)

    def side(x: int, value: int, label: str, sub: str) -> str:
        return (f'    <text x="{x}" y="148" font-size="38" font-weight="800" text-anchor="middle" fill="{FG}">{value:,}</text>\n'
                f'    <text x="{x}" y="180" font-size="16" text-anchor="middle" fill="{FG_DIM}">{label}</text>\n'
                f'    <text x="{x}" y="206" font-size="14" text-anchor="middle" fill="{COMMENT}">{escape(sub)}</text>')

    body = [
        f'    <style>.ring {{ animation: draw 1.2s ease-out both; }} @keyframes draw {{ from {{ stroke-dashoffset:{circ:.1f}; }} }}'
        f' @media (prefers-reduced-motion: reduce) {{ .ring {{ animation:none; }} }}</style>',
        f'    <line x1="205" y1="92" x2="205" y2="262" stroke="{LINE}"/><line x1="395" y1="92" x2="395" y2="262" stroke="{LINE}"/>',
        side(110, cal["totalContributions"], "contributions", since),
        f'    <circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{LINE}" stroke-width="6"/>',
        f'    <circle class="ring" cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{FG}" stroke-width="6" stroke-linecap="round"'
        f' stroke-dasharray="{circ:.1f}" stroke-dashoffset="{offset:.1f}" style="stroke-dashoffset:{offset:.1f}" transform="rotate(-90 {cx} {cy})"/>',
        f'    <circle cx="{cx}" cy="{cy - r}" r="17" fill="{BG}"/>',
        f'    <path transform="translate({cx - 12} {cy - r - 13})" d="{FLAME}" fill="{FG}"/>',
        f'    <text x="{cx}" y="{cy + 14}" font-size="40" font-weight="800" text-anchor="middle" fill="{FG}">{info["current_len"]}</text>',
        f'    <text x="{cx}" y="{cy + 92}" font-size="16" font-weight="700" text-anchor="middle" fill="{FG}">current streak</text>',
        f'    <text x="{cx}" y="{cy + 116}" font-size="14" text-anchor="middle" fill="{COMMENT}">{escape(cur_span)}</text>',
        side(490, info["longest_len"], "longest streak", span(info["longest"])),
    ]
    return frame(600, 300, "commit streak", "\n".join(body))


def langs_svg(u: dict) -> str:
    sizes: dict[str, int] = {}
    for repo in u["repositories"]["nodes"]:
        for e in repo["languages"]["edges"]:
            name = e["node"]["name"]
            if name not in IGNORED_LANGS:
                sizes[name] = sizes.get(name, 0) + e["size"]
    total = sum(sizes.values()) or 1
    top = sorted(sizes.items(), key=lambda kv: -kv[1])[:5]
    rest = total - sum(s for _, s in top)
    if rest > 0:
        top.append(("Other", rest))
    colors = {name: SHADES[i] if name != "Other" else LINE for i, (name, _) in enumerate(top)}

    body = ['    <clipPath id="bar"><rect x="32" y="76" width="536" height="12" rx="6"/></clipPath>',
            '    <g clip-path="url(#bar)">']
    x = 32.0
    for name, size in top:
        w = 536 * size / total
        body.append(f'      <rect x="{x:.2f}" y="76" width="{w + 0.5:.2f}" height="12" fill="{colors[name]}"/>')
        x += w
    body.append("    </g>")
    for i, (name, size) in enumerate(top):
        cx, cy = 32 + (i % 3) * 182, 128 + (i // 3) * 34
        body.append(
            f'    <circle cx="{cx + 6}" cy="{cy - 5}" r="6" fill="{colors[name]}"/>'
            f'<text x="{cx + 20}" y="{cy}" font-size="16" fill="{FG}">{escape(name)} '
            f'<tspan fill="{COMMENT}">{pct(100 * size / total)}</tspan></text>'
        )
    if not top:
        body.append(f'    <text x="32" y="124" font-size="15" fill="{COMMENT}">no public code yet</text>')

    # contributions per week, last 12 months
    weeks = [sum(d["contributionCount"] for d in wk["contributionDays"])
             for wk in u["contributionsCollection"]["contributionCalendar"]["weeks"]]
    body.append(f'    <text x="32" y="218" font-size="16" fill="{COMMENT}">contributions per week · last 12 months</text>')
    peak = max(weeks, default=0) or 1
    bw = 536 / max(len(weeks), 1)
    for i, n in enumerate(weeks):
        h = 3 + 39 * n / peak
        color = BLUE if n else LINE
        body.append(f'    <rect x="{32 + i * bw:.2f}" y="{276 - h:.1f}" width="{bw - 3:.2f}" height="{h:.1f}" rx="1.5" fill="{color}"/>')
    return frame(600, 300, "languages & rhythm", "\n".join(body))


CELL, GAP = 14, 4  # px
GRID_GREYS = ["#1a1a1a", "#3a3a3a", "#6b6b6b", "#a3a3a3", "#f5f5f5"]
ALIVE, AFTERGLOW = "#f5f5f5", ["#4d4d4d", "#2b2b2b"]  # dead cells fade out over two generations
GENS, HOLD_S, GEN_S, FADE_S, BACK_S = 48, 2.4, 0.42, 0.2, 1.2
# gliders in four directions, dropped on the busiest days whenever the board freezes
GLIDERS = [[(1, 0), (2, 1), (0, 2), (1, 2), (2, 2)], [(1, 0), (0, 1), (0, 2), (1, 2), (2, 2)],
           [(0, 0), (1, 0), (2, 0), (2, 1), (1, 2)], [(0, 0), (1, 0), (2, 0), (0, 1), (1, 2)]]


def levels(counts: list[int]) -> list[int]:
    """0..4 like GitHub's calendar: quartiles of the non-zero days."""
    nz = sorted(c for c in counts if c)
    if not nz:
        return [0] * len(counts)
    q = [nz[min(len(nz) - 1, int(len(nz) * f))] for f in (0.25, 0.5, 0.75)]
    return [0 if c == 0 else 1 + sum(c > t for t in q) for c in counts]


def life_generations(cells: list[tuple[int, int, int]], ncols: int) -> list[set]:
    """Conway's Game of Life on the calendar (wrapping at the edges), seeded with the active days.

    A real calendar is mostly one dense block that dies out in a couple of generations, so when
    the board goes empty or starts repeating, a glider is dropped on the next busiest day.
    """
    valid = {(c, r) for c, r, _ in cells}
    seed = {(c, r) for c, r, n in cells if n}
    spots = [(c, r) for c, r, n in sorted(cells, key=lambda t: (-t[2], t[0], t[1])) if n] or [(ncols // 2, 3)]

    def step(alive: set) -> set:
        near: dict = {}
        for c, r in alive:
            for dc in (-1, 0, 1):
                for dr in (-1, 0, 1):
                    if dc or dr:
                        k = ((c + dc) % ncols, (r + dr) % 7)
                        near[k] = near.get(k, 0) + 1
        return {p for p, k in near.items() if p in valid and (k == 3 or (k == 2 and p in alive))}

    gens, drops = [seed], 0
    for _ in range(GENS):
        nxt = step(gens[-1])
        if not nxt or nxt in gens[-6:]:
            c0, r0 = spots[drops % len(spots)]
            nxt |= {((c0 + x) % ncols, (r0 + y) % 7) for x, y in GLIDERS[drops % 4]} & valid
            drops += 1
        gens.append(nxt)
    return gens


def life_svg(u: dict) -> str:
    """The contribution graph comes to life (Game of Life), then settles back into the real graph."""
    weeks = u["contributionsCollection"]["contributionCalendar"]["weeks"]
    cells = []  # (col, row, count)
    for col, wk in enumerate(weeks):
        for d in wk["contributionDays"]:
            row = (date.fromisoformat(d["date"]).weekday() + 1) % 7  # Sunday on top, like GitHub
            cells.append((col, row, d["contributionCount"]))
    lv = levels([n for _, _, n in cells])
    ncols, pitch, pad = len(weeks), CELL + GAP, 24
    w, h = pad * 2 + ncols * pitch - GAP, pad * 2 + 7 * pitch - GAP
    gens = life_generations(cells, ncols)
    end = HOLD_S + GENS * GEN_S + 1.0
    total = end + BACK_S + 0.6

    def pct(t: float) -> str:
        return f"{100 * t / total:.2f}%"

    css, rects = [], []
    for i, (c, r, n) in enumerate(cells):
        orig = GRID_GREYS[lv[i]]
        states, since = [], 99  # colour per generation; `since` = generations since the cell died
        for g in gens:
            since = 0 if (c, r) in g else since + 1
            states.append(ALIVE if since == 0 else AFTERGLOW[since - 1] if since <= 2 else GRID_GREYS[0])
        cls = ""
        if any(s != orig for s in states):
            stops = [(0, orig), (HOLD_S - 0.5, orig), (HOLD_S, states[0])]
            for g in range(1, len(states)):
                if states[g] != states[g - 1]:
                    t = HOLD_S + g * GEN_S
                    stops += [(t, states[g - 1]), (t + FADE_S, states[g])]
            stops += [(end, states[-1]), (end + BACK_S, orig), (total, orig)]
            name = f"l{c}_{r}"
            css.append(f"@keyframes {name}{{{''.join(f'{pct(t)}{{fill:{col}}}' for t, col in stops)}}}")
            cls = f' style="animation-name:{name}"'
        rects.append(f'<rect x="{pad + c * pitch}" y="{pad + r * pitch}" width="{CELL}" height="{CELL}" rx="3" fill="{orig}"{cls}/>')

    css += [
        f"rect[style]{{animation-duration:{total:.2f}s;animation-iteration-count:infinite;animation-timing-function:linear}}",
        "@media (prefers-reduced-motion: reduce){rect[style]{animation:none}}",
    ]
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="Game of Life seeded with the contribution graph">
  <style>
{chr(10).join(css)}
  </style>
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{BG}"/><stop offset="1" stop-color="{BG_DARK}"/></linearGradient>
  </defs>
  <rect x=".5" y=".5" width="{w-1}" height="{h-1}" rx="8" fill="url(#bg)" stroke="{LINE}"/>
  {"".join(rects)}
</svg>
"""


def combine(svgs: list[str], vertical: bool, gap: int = 24, label: str = "") -> str:
    """Two cards in one image: side by side for desktop, stacked for phones
    (README swaps them with <picture>; an <img width="49%"> can't do that)."""
    import re

    sizes = [tuple(int(v) for v in re.search(r'width="(\d+)" height="(\d+)"', s).groups()) for s in svgs]
    if vertical:
        w, h = max(sw for sw, _ in sizes), sum(sh for _, sh in sizes) + gap * (len(svgs) - 1)
    else:
        w, h = sum(sw for sw, _ in sizes) + gap * (len(svgs) - 1), max(sh for _, sh in sizes)
    parts, pos = [], 0
    for s, (sw, sh) in zip(svgs, sizes):
        x, y = (0, pos) if vertical else (pos, 0)
        parts.append(s.replace('<svg xmlns="http://www.w3.org/2000/svg"', f'<svg x="{x}" y="{y}"', 1))
        pos += (sh if vertical else sw) + gap
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'role="img" aria-label="{escape(label)}">\n' + "".join(parts) + "</svg>\n")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="dist")
    ap.add_argument("--mock", help="read the user JSON from a file instead of the API")
    args = ap.parse_args()
    u = json.loads(Path(args.mock).read_text()) if args.mock else fetch()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "stats.svg").write_text(stats_svg(u))
    (out / "streak.svg").write_text(streak_svg(u))
    (out / "life.svg").write_text(life_svg(u))
    label = "GitHub activity and commit streak"
    (out / "activity.svg").write_text(combine([stats_svg(u), streak_svg(u)], vertical=False, label=label))
    (out / "activity-mobile.svg").write_text(
        combine([stats_svg(u, mobile=True), streak_svg(u, mobile=True)], vertical=True, label=label))
    print(f"wrote {out}/stats.svg, streak.svg, life.svg, activity.svg, activity-mobile.svg")


if __name__ == "__main__":
    main()
