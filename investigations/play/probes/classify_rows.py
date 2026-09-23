#!/usr/bin/env python3
"""Question answered: for every BLOCKING row the baseline gate printed for a Play
style, what is it, and what does the evidence say about where it comes from?

Reads the gate transcript (baseline/<Style>.gate.txt) and the two fonts it compared
(the release, and our conversion of the .sfd named in families.tsv), and writes one
TSV line per BLOCKING row: style, row, classification, evidence.

Classification rule (the reasoning is in FINDINGS.md, not in this script):
  OS/2.sx_height, OS/2.s_cap_height  -> converter-fidelity (tools/ff_heights_oracle.py
                                        reproduces the release from the .sfd)
  OS/2.us_weight_class               -> converter-fidelity (.sfd states TTFWeight)
  everything else                    -> provenance (the release is v2.101, built by
                                        Glyphs.app from m4rc1e/play sources/Play.glyphs)
For cmap rows it also records what the two glyphs are, so a reader can see that a
"rename" row is a redesigned glyph, not only a new name.

Usage: classify_rows.py <gate.txt> <release.ttf> <built.ttf> <Style>  > rows.tsv
"""
import re
import sys

from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib import TTFont

gate, rel_p, ours_p, style = sys.argv[1:5]
rel, ours = TTFont(rel_p), TTFont(ours_p)
crel, cours = rel.getBestCmap(), ours.getBestCmap()
grel, gours = rel.getGlyphSet(), ours.getGlyphSet()


def desc(font, gs, cm, u):
    g = cm.get(u)
    if g is None:
        return "absent"
    bp = BoundsPen(gs)
    gs[g].draw(bp)
    b = tuple(round(x) for x in bp.bounds) if bp.bounds else None
    return f"{g} adv={font['hmtx'][g][0]} bbox={b}"


CONV = {"OS/2.sx_height": "FontForge SFStandardHeight rule reproduces the release (ff_heights_oracle MATCH); converter fix in progress",
        "OS/2.s_cap_height": "FontForge SFStandardHeight rule reproduces the release (ff_heights_oracle MATCH); converter fix in progress",
        "OS/2.us_weight_class": ".sfd states TTFWeight: 700; fontc leaves 400 for a static single-master source; converter fix in progress"}
for line in open(gate, encoding="utf-8"):
    if not line.startswith("BLOCKING "):
        continue
    body = line[len("BLOCKING "):].rstrip("\n")
    m = re.match(r"cmap U\+([0-9A-F]+)(.*)", body)
    if m:
        u = int(m.group(1), 16)
        row = f"cmap U+{m.group(1)}"
        kind = "LOST" if "LOST" in m.group(2) else "renamed+redrawn"
        ev = f"{kind}; release: {desc(rel, grel, crel, u)}; ours: {desc(ours, gours, cours, u)}"
        print(f"{style}\t{row}\tprovenance\t{ev}")
        continue
    key = body.split(" ", 1)[0]
    cls = "converter-fidelity" if key in CONV else "provenance"
    ev = CONV.get(key, body[:200])
    print(f"{style}\t{key}\t{cls}\t{ev}")
