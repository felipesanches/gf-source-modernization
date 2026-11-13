#!/usr/bin/env python3
"""Question: where the Glyphs-source build and the shipped font draw different ink, is the
drawing different, or only overlaps / contour direction? Compares signed area and bounds per
glyph. Usage: outline_area.py <built.ttf> <shipped.ttf>
"""
import sys
from fontTools.ttLib import TTFont
from fontTools.pens.areaPen import AreaPen
from fontTools.pens.boundsPen import BoundsPen
a, b = TTFont(sys.argv[1]), TTFont(sys.argv[2]); ga, gb = a.getGlyphSet(), b.getGlyphSet()
n = same_bounds = flipped = 0
for g in b.getGlyphOrder():
    if g not in ga:
        continue
    pa, pb = AreaPen(ga), AreaPen(gb); ga[g].draw(pa); gb[g].draw(pb)
    ba, bb = BoundsPen(ga), BoundsPen(gb); ga[g].draw(ba); gb[g].draw(bb)
    if abs(pa.value - pb.value) > 200 or ba.bounds != bb.bounds:
        n += 1; same_bounds += ba.bounds == bb.bounds; flipped += pa.value * pb.value < 0
        if ba.bounds != bb.bounds:
            print("  bounds differ:", g, ba.bounds, bb.bounds)
print("%d of %d glyphs differ in signed area (>200) or bounds; %d have equal bounds; %d have opposite sign"
      % (n, len(b.getGlyphOrder()), same_bounds, flipped))
