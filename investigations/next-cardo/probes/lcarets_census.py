#!/usr/bin/env python3
"""Which styles does the LCarets2 -> caret anchor change touch, and does each release
carry the carets?

Question answered: for every style of a pairing table, how many glyphs of its .sfd
state an LCarets2 with a caret FontForge would export (non-zero, or any with
LigCaretCntFixed), and how many LigGlyph records the release's GDEF LigCaretList has.
A style with carets in the source and none in the release would be CHANGED by the
converter fix and must be looked at before the fix is adopted.

Usage: FAMILIES=<pairing.tsv> lcarets_census.py     (default: gf-source-modernization/families-next.tsv)
Prints: style, glyphs with exportable carets in the .sfd, LigGlyphs in the release.
Python: /home/fsanches/compartilhado/gftools/venv/bin/python3
"""
import os
import re
import sys

from fontTools.ttLib import TTFont

sys.path.insert(0, "/home/fsanches/compartilhado/gf-source-modernization/tools")
import recipe  # noqa: E402

for r in recipe.rows():
    try:
        text = recipe.source_text(r)
    except Exception:
        continue
    n = 0
    for body in re.findall(r"StartChar: .*?\n(.*?)EndChar", text, re.S):
        m = re.search(r"^LCarets2: (\d+)((?: -?\d+)*)", body, re.M)
        if not m:
            continue
        fixed = re.search(r"^LigCaretCntFixed: [1-9]", body, re.M) is not None
        vals = [int(v) for v in m.group(2).split()][:int(m.group(1))]
        if any(fixed or v != 0 for v in vals):
            n += 1
    rel = 0
    if os.path.exists(r["shipped"]):
        f = TTFont(r["shipped"])
        if "GDEF" in f and f["GDEF"].table.LigCaretList:
            rel = f["GDEF"].table.LigCaretList.LigGlyphCount
    if n or rel:
        print("%s\t%d\t%d" % (r["style"], n, rel))
