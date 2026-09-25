#!/usr/bin/env python3
"""In how many glyphs does a release's hmtx left side bearing disagree with its own glyf xMin?

Question answered: FontForge 2008 writes a glyph's hmtx lsb with
`putshort(gi->hmtx, b->minx)` (tottf.c ttfdumpmetrics) -- the UNROUNDED bounding box
truncated to an int -- while it writes the glyf points with rint() (tottf.c SSAddPoints).
When the outline's minimum x has a fractional part (an oblique made by skewing, or a
.sfd point at x.5), the two disagree by a unit, and a rasterizer, which places the
outline by the hmtx lsb (TrueType phantom points), draws the glyph a unit to the side.
A compiler that derives the lsb from the rounded glyf cannot reproduce that from any
source. Which glyphs of each release carry such a stale lsb, and which of them does
diffenator3 report as rendering differently?

Usage:
  stale_lsb.py <release.ttf> [<d3.json>]
Prints: total glyphs with lsb != xMin, the list, and (with d3.json) the overlap with
diffenator3's glyph rendering differences.
"""
import json
import sys

from fontTools.ttLib import TTFont


def main(release, d3=None):
    f = TTFont(release)
    glyf, hmtx = f["glyf"], f["hmtx"].metrics
    stale = {}
    for name in f.getGlyphOrder():
        g = glyf[name]
        if g.numberOfContours == 0:
            continue
        g.recalcBounds(glyf)
        if hmtx[name][1] != g.xMin:
            stale[name] = (hmtx[name][1], g.xMin)
    cmap = {v: k for k, v in (f.getBestCmap() or {}).items()}
    print("%s: %d glyph(s) whose hmtx lsb disagrees with glyf xMin" % (release, len(stale)))
    print("  " + " ".join("%s(lsb %d, xMin %d)" % (n, a, b) for n, (a, b) in sorted(stale.items())[:40]))
    if d3:
        d = json.load(open(d3))
        diffs = {ord(g["string"][0]) for L in d.get("locations") or [] for g in L.get("glyphs") or [] if g.get("string")}
        hit = [n for n in stale if cmap.get(n) in diffs]
        other = [("U+%04X" % cp) for cp in sorted(diffs) if (f.getBestCmap() or {}).get(cp) not in stale]
        print("  rendering diffs explained by a stale lsb: %d; rendering diffs not explained: %d %s" % (
            len(hit), len(other), " ".join(other[:30])))


if __name__ == "__main__":
    main(*sys.argv[1:3])
