#!/usr/bin/env python3
"""Draws stats.svg and langs.svg (Tokyo Night) from the GitHub GraphQL API.

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

BG, BG_DARK, LINE = "#1a1b26", "#16161e", "#292e42"
FG, FG_DIM, COMMENT = "#c0caf5", "#a9b1d6", "#565f89"
BLUE, CYAN, PURPLE, GREEN, ORANGE, RED, YELLOW = (
    "#7aa2f7", "#7dcfff", "#bb9af7", "#9ece6a", "#ff9e64", "#f7768e", "#e0af68",
)
MONO = "'JetBrains Mono','SFMono-Regular',Menlo,Consolas,'Liberation Mono',monospace"
LANG_COLORS = {
    "TypeScript": BLUE, "JavaScript": YELLOW, "Python": GREEN, "CSS": PURPLE,
    "HTML": ORANGE, "Shell": CYAN, "Kotlin": PURPLE, "Java": RED, "Dockerfile": CYAN,
}
FALLBACK = [CYAN, RED, "#73daca", "#b4f9f8", "#2ac3de"]
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


def streaks(days: list[dict]) -> tuple[int, int]:
    counts = {d["date"]: d["contributionCount"] for d in days}
    ordered = sorted(counts)
    longest = run = 0
    for d in ordered:
        run = run + 1 if counts[d] else 0
        longest = max(longest, run)
    day = date.fromisoformat(ordered[-1])
    if not counts.get(day.isoformat()):  # today not counted yet → start from yesterday
        day -= timedelta(days=1)
    current = 0
    while counts.get(day.isoformat()):
        current += 1
        day -= timedelta(days=1)
    return current, longest


def pct(v: float) -> str:
    return f"{v:.0f}%" if v >= 10 else f"{v:.1f}%"


def frame(w: int, h: int, title: str, body: str) -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{escape(title)}">
  <defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{BG}"/><stop offset="1" stop-color="{BG_DARK}"/></linearGradient></defs>
  <rect x=".5" y=".5" width="{w-1}" height="{h-1}" rx="16" fill="url(#bg)" stroke="{LINE}"/>
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
    current, longest = streaks(days)
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
        f'    <text x="32" y="{y + 6}" font-size="17" fill="{FG_DIM}">current streak '
        f'<tspan fill="{GREEN}" font-weight="700">{current}d</tspan>'
        f'<tspan fill="{COMMENT}">  ·  </tspan>longest '
        f'<tspan fill="{PURPLE}" font-weight="700">{longest}d</tspan>'
        f'<tspan fill="{COMMENT}">  ·  last 12 months</tspan></text>'
    )
    return frame(600, 300, "github activity", "\n".join(body))


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
    colors, fb = {}, iter(FALLBACK)
    for name, _ in top:
        colors[name] = COMMENT if name == "Other" else LANG_COLORS.get(name) or next(fb, CYAN)

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
    (out / "langs.svg").write_text(langs_svg(u))
    print(f"wrote {out}/stats.svg, {out}/langs.svg")


if __name__ == "__main__":
    main()
