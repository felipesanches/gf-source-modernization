#!/usr/bin/env python3
"""point_counts.py -- does the build carry exactly the release's glyf points?

Question answered: for one shipped/built pair, which glyphs differ in contour count,
point count, on/off-curve flags or coordinates (after sorting nothing: point order
as stored), and what exactly differs? diffenator3's rendering diff can miss a point
that does not move the outline (a duplicate or colinear on-curve point), and the
fontspector outline checks (outline_colinear_vectors, outline_short_segments) react
to exactly such points.

Run:
  PY=/home/fsanches/compartilhado/gftools/venv/bin/python3
  $PY point_counts.py <shipped.ttf> <built.ttf>
Glyphs are matched by Unicode first (the build uses production names), then by name.
"""
import sys
from fontTools.ttLib import TTFont


def pts(font, name):
    g = font["glyf"][name]
    if g.isComposite():
        return ("composite", [(c.glyphName, c.x, c.y) for c in g.components])
    if g.numberOfContours == 0:
        return ("empty", [])
    coords, ends, flags = g.getCoordinates(font["glyf"])
    out, s = [], 0
    for e in ends:
        out.append([(x, y, f & 1) for (x, y), f in zip(coords[s:e + 1], flags[s:e + 1])])
        s = e + 1
    return ("simple", out)


def main():
    a, b = TTFont(sys.argv[1]), TTFont(sys.argv[2])
    ca, cb = a.getBestCmap(), b.getBestCmap()
    rb = {v: k for k, v in cb.items()}
    pairs = {}
    for cp, n in ca.items():
        if cp in cb:
            pairs[n] = cb[cp]
    for n in a.getGlyphOrder():
        if n not in pairs and n in b.getGlyphOrder():
            pairs[n] = n
    tot_a = tot_b = 0
    for na, nb in sorted(pairs.items()):
        ka, pa = pts(a, na)
        kb, pb = pts(b, nb)
        if ka == "simple":
            tot_a += sum(len(c) for c in pa)
        if kb == "simple":
            tot_b += sum(len(c) for c in pb)
        if ka != kb:
            print("%s/%s: kind %s vs %s" % (na, nb, ka, kb))
            continue
        if ka != "simple":
            continue
        if [len(c) for c in pa] != [len(c) for c in pb] or pa != pb:
            # compare contours as cyclic sequences (start point may move) and by direction
            def canon(c):
                rots = [tuple(c[i:] + c[:i]) for i in range(len(c))]
                rrots = [tuple(list(reversed(c))[i:] + list(reversed(c))[:i]) for i in range(len(c))]
                return min(rots + rrots) if c else ()
            sa = sorted(canon(c) for c in pa)
            sb = sorted(canon(c) for c in pb)
            same = "same up to start point/direction" if sa == sb else "DIFFERENT"
            print("%s/%s: contours %s vs %s -> %s" % (na, nb, [len(c) for c in pa], [len(c) for c in pb], same))
            if sa != sb:
                for i, (x, y) in enumerate(zip(pa, pb)):
                    if canon(x) != canon(y):
                        print("   contour %d shipped %s" % (i, x))
                        print("   contour %d built   %s" % (i, y))
    unmatched = sorted(set(a.getGlyphOrder()) - set(pairs))
    print("unmatched shipped glyphs: %s" % unmatched)
    print("total simple points (matched glyphs): shipped %d built %d" % (tot_a, tot_b))


if __name__ == "__main__":
    main()
