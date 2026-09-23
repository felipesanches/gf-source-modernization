#!/usr/bin/env python3
"""Question answered: does our build of Corben-Bold carry the release's drawings and
advances, glyph by glyph (paired by NAME)?

Point-for-point equality is the wrong test here: the release's quadratic curves are
FontForge's own cubic->quadratic conversion (2011), ours are fontc's, so off-curve
points differ on almost every curved glyph. Instead, per glyph:
  advance     hmtx advance equal
  bounds      tight bounds (BoundsPen, the curve's real extrema) equal within 1 unit
  area        signed-area magnitude equal within 0.5 %
Prints counts and lists every glyph that fails a test.
Usage: gftools/venv/bin/python3 outline_compare.py <shipped.ttf> <built.ttf>
"""
import sys
from fontTools.ttLib import TTFont
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.areaPen import AreaPen

S, B = TTFont(sys.argv[1]), TTFont(sys.argv[2])
sg, bg = S.getGlyphSet(), B.getGlyphSet()


def measure(gs, n):
    bp, ap = BoundsPen(gs), AreaPen(gs)
    gs[n].draw(bp)
    gs[n].draw(ap)
    return bp.bounds, abs(ap.value)


names = [n for n in S.getGlyphOrder() if n in bg]
adv, bnd, area = [], [], []
for n in names:
    if S["hmtx"][n][0] != B["hmtx"][n][0]:
        adv.append(n)
    (sb, sa), (bb, ba) = measure(sg, n), measure(bg, n)
    if (sb is None) != (bb is None) or (sb and max(abs(x - y) for x, y in zip(sb, bb)) > 1):
        bnd.append((n, sb, bb))
    if sa or ba:
        if abs(sa - ba) > 0.005 * max(sa, ba):
            area.append((n, round(sa), round(ba)))
print("common glyphs %d; only in release %s; only in build %s"
      % (len(names), sorted(set(S.getGlyphOrder()) - set(bg.keys())),
         sorted(set(B.getGlyphOrder()) - set(sg.keys()))))
print("advance differs: %d %s" % (len(adv), adv))
print("tight bounds differ (>1 unit): %d %s" % (len(bnd), bnd))
print("area differs (>0.5%%): %d %s" % (len(area), area))
