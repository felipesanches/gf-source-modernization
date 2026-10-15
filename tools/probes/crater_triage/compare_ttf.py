#!/usr/bin/env python3
"""Question answered: is a TTF built from a new upstream source the same design as the shipped
one? Compares two fonts by codepoint: version, glyph and cmap counts, advance widths, glyph
bounding boxes (differences over 2 units), codepoints only in one, GPOS lookup counts.

  compare_ttf.py <shipped.ttf> <other.ttf>
"""
import sys
from fontTools.ttLib import TTFont
from fontTools.pens.boundsPen import BoundsPen

a, b = TTFont(sys.argv[1]), TTFont(sys.argv[2])
for name, f in (("shipped", a), ("other", b)):
    print(name, f["name"].getDebugName(5), "glyphs", len(f.getGlyphOrder()), "cmap", len(f.getBestCmap()))
ca, cb = a.getBestCmap(), b.getBestCmap()
ga, gb = a.getGlyphSet(), b.getGlyphSet()
shared = sorted(set(ca) & set(cb))
adv = bbox = 0
for cp in shared:
    if ga[ca[cp]].width != gb[cb[cp]].width:
        adv += 1
    pa, pb = BoundsPen(ga), BoundsPen(gb)
    ga[ca[cp]].draw(pa)
    gb[cb[cp]].draw(pb)
    if pa.bounds and pb.bounds and max(abs(x - y) for x, y in zip(pa.bounds, pb.bounds)) > 2:
        bbox += 1
print("shared codepoints", len(shared), "advance differs", adv, "bbox differs by >2 units", bbox)
print("only shipped:", " ".join("U+%04X" % c for c in sorted(set(ca) - set(cb))))
print("only other:", " ".join("U+%04X" % c for c in sorted(set(cb) - set(ca))))
for name, f in (("shipped", a), ("other", b)):
    print(name, "GPOS lookups", len(f["GPOS"].table.LookupList.Lookup) if "GPOS" in f else 0)
