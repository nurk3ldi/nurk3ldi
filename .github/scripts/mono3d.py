#!/usr/bin/env python3
"""Recolours the language pie of the 3D contribution graph to greys.

github-profile-3d-contrib always paints languages in GitHub's colours; the
rest of the profile is black & white, so every colour that is not part of
.github/profile-3d-settings.json is mapped to a grey, in order of appearance.

    python3 .github/scripts/mono3d.py dist/profile-3d.svg
"""
import json
import re
import sys
from pathlib import Path

SHADES = ["#fafafa", "#a3a3a3", "#6b6b6b", "#474747", "#333333", "#262626"]

settings = json.loads(Path(".github/profile-3d-settings.json").read_text())
theme = {v.lower() for k, v in settings.items() if isinstance(v, str) and v.startswith("#")}
theme |= {c.lower() for c in settings["contribColors"]}

svg_path = Path(sys.argv[1])
svg = svg_path.read_text()
mapping: dict[str, str] = {}
for m in re.finditer(r'fill(?:="|:\s*)(#[0-9a-fA-F]{6})', svg):
    colour = m.group(1).lower()
    if colour not in theme and colour not in mapping:
        mapping[colour] = SHADES[min(len(mapping), len(SHADES) - 1)]
for colour, grey in mapping.items():
    svg = re.sub(re.escape(colour), grey, svg, flags=re.IGNORECASE)
svg_path.write_text(svg)
print(f"recoloured {len(mapping)} language colours: {mapping}")
