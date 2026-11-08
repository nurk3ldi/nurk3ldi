#!/usr/bin/env python3
"""Draws stats.svg and streak.svg (Tokyo Night) from the GitHub GraphQL API.

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


def frame(w: int, h: int, title: str, body: str) -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{escape(title)}">
  <defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{BG}"/><stop offset="1" stop-color="{BG_DARK}"/></linearGradient></defs>
  <rect x=".5" y=".5" width="{w-1}" height="{h-1}" rx="8" fill="url(#bg)" stroke="{LINE}"/>
  <g font-family="{MONO}">
    <text x="32" y="50" font-size="21" font-weight="700" fill="{FG}"><tspan fill="{BLUE}">❯ </tspan>{escape(title)}</text>
{body}
  </g>
</svg>
"""


def stats_svg(u: dict) -> str:
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


def streak_svg(u: dict) -> str:
    cal = u["contributionsCollection"]["contributionCalendar"]
    days = [d for wk in cal["weeks"] for d in wk["contributionDays"]]
    info = streak_info(days)
    cx, cy, r = 300, 150, 58
    circ = 2 * 3.14159 * r
    # the ring fills to current / longest streak
    filled = info["current_len"] / info["longest_len"] if info["longest_len"] else 0
    offset = circ * (1 - filled)
    since = f"since {fmt(info['first'])}, {info['first'].year}" if info["first"] else "last 12 months"
    cur = info["current"]
    cur_span = (f"{fmt(cur[0])} – today" if cur and cur[0] != cur[1] else "today") if cur else "start one today"

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
    print(f"wrote {out}/stats.svg, {out}/streak.svg")


if __name__ == "__main__":
    main()
