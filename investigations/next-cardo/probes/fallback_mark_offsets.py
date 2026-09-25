#!/usr/bin/env python3
"""How large are the base+mark shaping differences of a font with no GPOS mark lookups?

Question answered: Cardo-Bold and Cardo-Italic have no mark attachment in either the
release or our build, so HarfBuzz places a combining mark by its fallback positioning,
which reads each glyph's extents from its glyf HEADER bounding box. Where the two fonts'
headers differ (FontForge 20110222 and fontc compute a composite glyph's box
differently, and the release's boxes are stale -- RELEASE-STALE bearings), the mark
lands elsewhere although both outlines are the same. For each differing base+mark
string (probes/shaping_compare.py corpus), how far apart do the glyphs land (maximum
absolute-position delta), and which marks are involved? Also prints, for the worst
case, both fonts' header box and outline bounds of every glyph involved.

Usage:
  fallback_mark_offsets.py <shipped.ttf> <built.ttf>
Python: /home/fsanches/compartilhado/gftools/venv/bin/python3
"""
import collections
import os
import sys
import unicodedata

from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib import TTFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import shaping_compare as sc  # noqa: E402


def boxes(path, cps):
    f = TTFont(path)
    cm, gs = f.getBestCmap(), f.getGlyphSet()
    out = {}
    for cp in cps:
        n = cm[cp]
        g = f["glyf"][n]
        bp = BoundsPen(gs)
        gs[n].draw(bp)
        out["U+%04X" % cp] = (n, (g.xMin, g.yMin, g.xMax, g.yMax),
                             tuple(round(v) for v in bp.bounds) if bp.bounds else None,
                             "composite" if g.isComposite() else "simple")
    return out


def main():
    shipped, built = sys.argv[1], sys.argv[2]
    S, B = sc.Shaper(shipped), sc.Shaper(built)
    shared = set(TTFont(shipped).getBestCmap()) & set(TTFont(built).getBestCmap())
    bases = [c for c in shared if unicodedata.category(chr(c)).startswith("L") and sc.script_of(c)]
    marks = [c for c in shared if unicodedata.category(chr(c)) in ("Mn", "Mc")]
    hist, bymark, worst = collections.Counter(), collections.Counter(), (0, None, None, None)
    for b in bases:
        for m in marks:
            t = chr(b) + chr(m)
            a, o = S.run(t), B.run(t)
            if a == o:
                continue
            if [x[0] for x in a] != [x[0] for x in o]:
                hist["different glyphs"] += 1
                continue
            d = max(max(abs(x[1] - y[1]), abs(x[2] - y[2])) for x, y in zip(a, o))
            hist["<=2" if d <= 2 else "3..10" if d <= 10 else ">10"] += 1
            bymark["U+%04X" % m] += 1
            if d > worst[0]:
                worst = (d, t, a, o)
    print("differing base+mark strings by maximum position delta: %s" % dict(hist))
    print("marks involved: %d %s" % (len(bymark), bymark.most_common(20)))
    if worst[1]:
        print("worst %d units: %s\n  release %s\n  ours    %s" % (
            worst[0], " ".join("U+%04X" % ord(c) for c in worst[1]), sc.fmt(worst[2]),
            sc.fmt(worst[3])))
        cps = [ord(c) for c in worst[1]]
        for lab, p in (("release", shipped), ("ours", built)):
            for k, v in boxes(p, cps).items():
                print("  %s %s %s header %s outline %s %s" % (lab, k, v[0], v[1], v[2], v[3]))


if __name__ == "__main__":
    main()
