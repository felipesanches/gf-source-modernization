#!/usr/bin/env python3
"""Question answered: how much of Play's DESIGN differs between two fonts?

Pairs glyphs by codepoint (never by name -- names changed between v1 and v2) and
counts: codepoints only in A / only in B, glyph totals, advances that differ, and
outlines that differ. An outline "differs" when, after decomposing components, its
bounding box moves by more than 2 units on any side or its signed area changes by
more than 1% -- point order, start point and curve-type conversion (FontForge's own
quadratics vs cu2qu) are deliberately NOT counted, they are not design changes.

Usage: design_delta.py <A.ttf> <B.ttf>
  e.g. A = the release google/fonts ofl/play/Play-Regular.ttf (v2.101)
       B = our conversion of the .sfd, or the hg-era binary (v1.002)
"""
import sys
from fontTools.ttLib import TTFont
from fontTools.pens.areaPen import AreaPen
from fontTools.pens.boundsPen import BoundsPen


def load(p):
    f = TTFont(p)
    return f, f.getBestCmap() or {}, f.getGlyphSet()


def shape(gs, name):
    bp, ap = BoundsPen(gs), AreaPen(gs)
    gs[name].draw(bp)
    gs[name].draw(ap)
    return bp.bounds, abs(ap.value)


def differs(sa, sb):
    (ba, aa), (bb, ab) = sa, sb
    if ba is None or bb is None:
        return (ba is None) != (bb is None)
    if max(abs(x - y) for x, y in zip(ba, bb)) > 2:
        return True
    return abs(aa - ab) > 0.01 * max(aa, ab, 1)


a, ca, ga = load(sys.argv[1])
b, cb, gb = load(sys.argv[2])
common = sorted(set(ca) & set(cb))
adv = [u for u in common if a["hmtx"][ca[u]][0] != b["hmtx"][cb[u]][0]]
out = [u for u in common if differs(shape(ga, ca[u]), shape(gb, cb[u]))]
print(f"A {sys.argv[1]}: {len(a.getGlyphOrder())} glyphs, {len(ca)} codepoints, version {a['name'].getDebugName(5)!r}")
print(f"B {sys.argv[2]}: {len(b.getGlyphOrder())} glyphs, {len(cb)} codepoints, version {b['name'].getDebugName(5)!r}")
print(f"codepoints only in A: {len(set(ca)-set(cb))}; only in B: {len(set(cb)-set(ca))}; common: {len(common)}")
print(f"common codepoints with a different advance: {len(adv)}")
print(f"common codepoints with a different outline: {len(out)}")
print("  first 40 differing outlines:", " ".join(f"U+{u:04X}" for u in out[:40]))
