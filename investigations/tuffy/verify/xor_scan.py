#!/usr/bin/env python3
"""Adversarial verification, unit "tuffy".

Question it answers: independent of table_gate.py's measures (advance, bbox within
2 units, per-contour |area| within 0.4%), which codepoints DRAW differently in two
fonts? The drawing is compared as filled regions (nonzero rule): area of the
symmetric difference ((A-B)+(B-A), skia-pathops) relative to the larger filled area.

Usage: xor_scan.py <release.ttf> <built.ttf> [--min 0.005] [--cps U+XXXX,...]
Prints one line per codepoint whose advance differs or whose XOR ratio >= --min,
sorted by ratio, then a summary line "N codepoint(s) compared, M differ".
"""
import sys
import pathops
from fontTools.ttLib import TTFont
from fontTools.pens.areaPen import AreaPen


def region(font, name):
    gs = font.getGlyphSet()
    p = pathops.Path()
    gs[name].draw(p.getPen(glyphSet=gs))
    # resolve overlaps under the nonzero rule, as a rasteriser fills it
    p.simplify(fix_winding=True)
    return p


def area(path):
    ap = AreaPen()
    path.draw(ap)
    return abs(ap.value)


def main():
    a, b = sys.argv[1], sys.argv[2]
    mn = 0.005
    cps = None
    if "--min" in sys.argv:
        mn = float(sys.argv[sys.argv.index("--min") + 1])
    if "--cps" in sys.argv:
        cps = [int(x[2:], 16) for x in sys.argv[sys.argv.index("--cps") + 1].split(",")]
    fa, fb = TTFont(a), TTFont(b)
    ca, cb = fa.getBestCmap(), fb.getBestCmap()
    shared = sorted(set(ca) & set(cb)) if cps is None else cps
    out = []
    for cp in shared:
        na, nb = ca[cp], cb[cp]
        adva, advb = fa["hmtx"][na][0], fb["hmtx"][nb][0]
        ra, rb = region(fa, na), region(fb, nb)
        A, B = area(ra), area(rb)
        # symmetric difference as (A - B) + (B - A); measuring pathops' XOR output
        # directly is wrong (its pieces come back with mixed winding and cancel)
        X = (area(pathops.op(ra, rb, pathops.PathOp.DIFFERENCE, fix_winding=True))
             + area(pathops.op(rb, ra, pathops.PathOp.DIFFERENCE, fix_winding=True)))
        ratio = X / max(A, B, 1.0)
        if adva != advb or ratio >= mn:
            out.append((ratio, cp, na, nb, adva, advb, A, B, X))
    for ratio, cp, na, nb, adva, advb, A, B, X in sorted(out, reverse=True):
        print("U+%04X %-24s %-24s adv %5d %5d  area %9.0f %9.0f  xor %8.0f  ratio %.4f"
              % (cp, na, nb, adva, advb, A, B, X, ratio))
    print("%d codepoint(s) compared, %d differ (advance, or XOR >= %.3f of area)"
          % (len(shared), len(out), mn))


if __name__ == "__main__":
    main()
