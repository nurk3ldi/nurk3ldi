#!/usr/bin/env python3
"""Keeps only the 3D contribution city of github-profile-3d-contrib's image.

The tool always adds a radar chart, a language pie and totals; this drops every
top-level group except the 3D calendar (the one with the most children), crops
the canvas to it and frames it like the other profile cards.

    python3 .github/scripts/minimal3d.py dist/profile-3d.svg
"""
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", NS)
ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")

# calendar sits at x 20..1216, y 144..826 of the 1280x850 canvas; the top margin
# leaves room for bars of up to ~80 contributions/day at the far corner
X, Y, W, H = 10, 40, 1216, 800
BORDER = "#262626"

path = Path(sys.argv[1])
tree = ET.parse(path)
root = tree.getroot()
groups = [el for el in root if el.tag == f"{{{NS}}}g"]
city = max(groups, key=lambda g: len(list(g)))
for g in groups:
    if g is not city:
        root.remove(g)

root.set("viewBox", f"{X} {Y} {W} {H}")
root.set("width", str(W))
root.set("height", str(H))
for el in root:
    if el.tag == f"{{{NS}}}rect" and el.get("class") == "fill-bg":
        el.attrib.update(x=str(X + 0.5), y=str(Y + 0.5), width=str(W - 1), height=str(H - 1), rx="8",
                         stroke=BORDER)
        break
tree.write(path, encoding="unicode")
print(f"kept 1 of {len(groups)} groups, cropped to {W}x{H}")
