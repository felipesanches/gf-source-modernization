#!/usr/bin/env python3
"""Question answered: is FontForge's rounding rule actually needed, or would plain
per-point rounding of the scaled coordinates (rint(v * 1024/1000) for every on- and
off-curve point, implied points left implied) reproduce the release just as well?

Counts, per style, the simple glyphs whose TrueType points differ from the release
under the naive rule. Compare with verify_scaled_points.py (FontForge's rule: 0).
Usage: naive_rounding_check.py <unmodified.sfd> <release.ttf> [--implied-midpoints]
  --implied-midpoints  keep FontForge's treatment of implied on-curve points (the
                       midpoint of their rounded controls) and round everything
                       else independently, isolating the offset-rounding rule
"""
import sys
from fontTools.ttLib import TTFont
sys.path.insert(0, __import__("os").path.dirname(__file__))
import ff_scale_em as fse
import verify_scaled_points as v

src, rel = sys.argv[1:3]
MID = "--implied-midpoints" in sys.argv
text = open(src, encoding="latin-1").read()
# run the real scaler to get widths/refs, then rebuild outlines naively
glyphs = v.read_sfd(src)
f = TTFont(rel); glyf = f["glyf"]
diff = total = 0
for name, g in glyphs.items():
    rg = glyf[name]
    if rg.isComposite() or g["refs"] or not g["contours"]:
        continue
    total += 1
    for pts, closed, _ in g["contours"]:
        for p in pts:
            p.me = (round(p.me[0] * 1.024), round(p.me[1] * 1.024))
            p.nextcp = (round(p.nextcp[0] * 1.024), round(p.nextcp[1] * 1.024))
            p.prevcp = (round(p.prevcp[0] * 1.024), round(p.prevcp[1] * 1.024))
        if MID:
            for p in pts:
                if p.ttf == 0xFFFF:   # implied point: midpoint of its rounded controls
                    p.me = ((p.nextcp[0] + p.prevcp[0]) / 2, (p.nextcp[1] + p.prevcp[1]) / 2)
    mine = v.emit(g["contours"])
    coords, ends, flags = rg.getCoordinates(glyf)
    theirs, start = [], 0
    for e in ends:
        theirs.append([(coords[k][0], coords[k][1], flags[k] & 1) for k in range(start, e + 1)])
        start = e + 1
    if mine != theirs:
        diff += 1
print("%s%s: naive per-point rounding differs from the release on %d of %d simple glyphs"
      % (src.split("/")[-1], " (implied midpoints)" if MID else "", diff, total))
