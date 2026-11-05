#!/usr/bin/env python3
"""How many instructed glyphs would fontc lose points of, once the source keeps the release's
own points? write-fonts (glyf/simple.rs is_implicit_on_curve) drops every on-curve point that
lies between two off-curves, at their midpoint (exactly, or after rounding both sides). A
release's programs address points by index, so an explicit midpoint on-curve the release
kept and fontc drops moves every later point of that glyph.

Usage: midpoints.py census.tsv <google/fonts dir>  (instructed releases only, as predict.py)
Prints per font: instructed glyphs, of them with at least one such point, and the points.
"""
import csv
import os
import sys

from fontTools.ttLib import TTFont


def droppable(coords, flags, ends):
    n, start = 0, 0
    for end in ends:
        idx = list(range(start, end + 1))
        m = len(idx)
        for k in range(m):
            i, p, q = idx[k], idx[k - 1], idx[(k + 1) % m]
            if flags[i] & 1 and not flags[p] & 1 and not flags[q] & 1:
                (x0, y0), (x1, y1), (x2, y2) = coords[p], coords[i], coords[q]
                if x0 + x2 == 2 * x1 and y0 + y2 == 2 * y1:
                    n += 1
        start = end + 1
    return n


def main():
    rows = list(csv.DictReader(open(sys.argv[1]), delimiter="\t"))
    tot_g = tot_hit = tot_pts = fonts = fonts_hit = 0
    for r in rows:
        instructed = r["class"] in ("other", "ttfautohint") or (r["smart_dropout"] != "exact" and r["prep"] != "-")
        if not instructed:
            continue
        path = next((os.path.join(sys.argv[2], lic, r["repo"], r["font"]) for lic in ("ofl", "apache", "ufl")
                     if os.path.exists(os.path.join(sys.argv[2], lic, r["repo"], r["font"]))), None)
        if not path:
            continue
        tt = TTFont(path)
        glyf = tt["glyf"]
        g_n = hit = pts = 0
        for name in tt.getGlyphOrder():
            g = glyf[name]
            if g.isComposite() or g.numberOfContours <= 0 or not (hasattr(g, "program") and g.program.getBytecode()):
                continue
            g_n += 1
            c = droppable(list(g.coordinates), list(g.flags), list(g.endPtsOfContours))
            if c:
                hit += 1
                pts += c
        fonts += 1
        fonts_hit += bool(hit)
        tot_g, tot_hit, tot_pts = tot_g + g_n, tot_hit + hit, tot_pts + pts
        print("%-22s %-40s %5d instructed glyphs, %4d with droppable points (%d points)" % (r["repo"], r["font"], g_n, hit, pts))
    print("TOTAL %d fonts (%d affected): %d instructed simple glyphs, %d with an explicit midpoint on-curve (%d points)"
          % (fonts, fonts_hit, tot_g, tot_hit, tot_pts))


main()
