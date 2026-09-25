#!/usr/bin/env python3
"""Which Yellowtail input carries the outlines Google Fonts ships?

Question answered: the shipped Yellowtail-Regular.ttf (google/fonts b5efa9c32e8f) versus
(a) hg 52f780b apache/yellowtail/src/Yellowtail-Regular-TTF.sfd, which is really a Type 1
PFB, and (b) the designer's Yellowtail-Regular.otf in the same tree: for each codepoint,
compare the glyph's signed area and bounding box. Counts codepoints whose area differs
by more than 0.1% / 0.4% and whose bbox differs by more than 1 unit.

Run: python3 yellowtail_outline_match.py <shipped.ttf> <yt.pfb> <yt.otf>
"""
import sys
from fontTools.ttLib import TTFont
from fontTools.t1Lib import T1Font
from fontTools.pens.areaPen import AreaPen
from fontTools.pens.boundsPen import BoundsPen


def stats(gs, name):
    a, b = AreaPen(gs), BoundsPen(gs)
    gs[name].draw(a); gs[name].draw(b)
    return abs(a.value), b.bounds


def compare(label, ref_gs, ref_cmap, gs, cmap):
    n = a01 = a04 = bb = 0
    for cp, gn in sorted(ref_cmap.items()):
        if cp not in cmap:
            continue
        ra, rb = stats(ref_gs, gn)
        oa, ob = stats(gs, cmap[cp])
        n += 1
        if ra and abs(oa - ra) / ra > 0.001: a01 += 1
        if ra and abs(oa - ra) / ra > 0.004: a04 += 1
        if (rb is None) != (ob is None) or (rb and any(abs(x - y) > 1 for x, y in zip(rb, ob))): bb += 1
    print("%s: %d codepoints compared; area off >0.1%%: %d, >0.4%%: %d; bbox off >1u: %d" % (label, n, a01, a04, bb))


ship = TTFont(sys.argv[1]); sgs = ship.getGlyphSet(); scm = ship.getBestCmap()
t1 = T1Font(sys.argv[2]); t1.parse()
cs = t1.font["CharStrings"]
enc = t1.font.get("Encoding")
from fontTools import agl
pcm = {}
for gn in cs.keys():
    u = agl.toUnicode(gn)
    if len(u) == 1: pcm[ord(u)] = gn
compare("PFB vs shipped", sgs, scm, cs, pcm)
otf = TTFont(sys.argv[3]); compare("designer OTF vs shipped", sgs, scm, otf.getGlyphSet(), otf.getBestCmap())
