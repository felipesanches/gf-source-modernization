#!/usr/bin/env python3
"""Question answered: why does the released Puritan-Italic carry hhea.ascender and
usWinAscent 880 when its own outlines reach 881 (Scaron)?

Hypothesis: FontForge's in-memory `f.em = 1024` scaled Scaron (iso8859-15 slot
0xA6) BEFORE caron (unencoded, slot > 255). A reference to a selected glyph only
has its OFFSET scaled (fontviewbase.c SCTransLayer), so Scaron's cached reference
bounding box became the UNSCALED caron plus the scaled offset, and nothing
refreshed it after caron itself was scaled. The exporter took the composite's
glyph header, and the font bbox that the offset-mode Win/Hhead ascents add to,
from that stale box.

Prints, for every composite in the release: its glyf header bbox, the bbox of its
resolved points, and the header bbox predicted by the hypothesis (referenced
glyph's UNSCALED point bbox + offset scaled but not rounded, floor/ceil).
Usage: stale_composite_bbox.py <unmodified.sfd> <release.ttf>
"""
import math
import sys
from fontTools.ttLib import TTFont
sys.path.insert(0, __import__("os").path.dirname(__file__))
import verify_scaled_points as v

src, rel = sys.argv[1:3]
gl = v.read_sfd(src)
f = TTFont(rel); glyf = f["glyf"]
S = 1024 / 1000


def pts_bbox(g):
    xs, ys = [], []
    for pts, closed, _ in g["contours"]:
        for p in pts:
            for q in (p.me, p.nextcp, p.prevcp):
                xs.append(q[0]); ys.append(q[1])
    return (min(xs), min(ys), max(xs), max(ys)) if xs else None


# raw (unscaled) reference offsets from the unmodified .sfd
for name, g in gl.items():
    if not g["refs"]:
        continue
    rg = glyf[name]
    c, _, _ = rg.getCoordinates(glyf)
    res = (min(x for x, y in c), min(y for x, y in c), max(x for x, y in c), max(y for x, y in c))
    boxes = []
    for rname, dx, dy in g["refs"]:
        b = pts_bbox(gl[rname])
        if b is None:
            continue
        ox, oy = dx * S, dy * S
        boxes.append((b[0] + ox, b[1] + oy, b[2] + ox, b[3] + oy))
    pred = (math.floor(min(b[0] for b in boxes)), math.floor(min(b[1] for b in boxes)),
            math.ceil(max(b[2] for b in boxes)), math.ceil(max(b[3] for b in boxes)))
    hdr = (rg.xMin, rg.yMin, rg.xMax, rg.yMax)
    print("%-12s header %-22s resolved %-22s predicted %-22s %s"
          % (name, hdr, res, pred, "PREDICTED" if pred == hdr else ("header==resolved" if hdr == res else "neither")))
