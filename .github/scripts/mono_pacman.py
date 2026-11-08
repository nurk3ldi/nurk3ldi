#!/usr/bin/env python3
"""Turns the GitHub-green grid of the Pac-Man graph into the profile's greys.

Pac-Man and the ghosts keep their colours; only the contribution cells,
background and labels are remapped.

    python3 .github/scripts/mono_pacman.py dist/pacman-contribution-graph-dark.svg
"""
import re
import sys
from pathlib import Path

GREYS = {
    "#0d1117": "#0a0a0a",  # background
    "#161b22": "#1a1a1a",  # no contributions
    "#0e4429": "#3a3a3a",
    "#006d32": "#6b6b6b",
    "#26a641": "#a3a3a3",
    "#39d353": "#f5f5f5",  # most contributions
    "#8b949e": "#737373",  # month labels
}

path = Path(sys.argv[1])
svg = path.read_text()
for green, grey in GREYS.items():
    svg = re.sub(re.escape(green), grey, svg, flags=re.IGNORECASE)
path.write_text(svg)
print("recoloured", path)
