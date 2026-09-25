#!/usr/bin/env python3
"""start_point_rotation.py -- does the build start each contour where FontForge's export did?

Question answered: for a shipped/built pair (glyphs matched by codepoint), for every
simple-glyph contour with the same points cyclically, by how many positions is the
built contour's point list rotated against the shipped one (0 = same start point)?
A rotation leaves rendering unchanged, but it moves a FontForge closing duplicate
point (first == last) into the middle of the contour, where it becomes a zero-length
segment that fontspector's outline_colinear_vectors / outline_short_segments count.

Run: $PY start_point_rotation.py <shipped.ttf> <built.ttf> [...more pairs]
"""
import sys
from collections import Counter

from fontTools.ttLib import TTFont


def contours(font, name):
    g = font["glyf"][name]
    if g.isComposite() or g.numberOfContours <= 0:
        return []
    c, ends, fl = g.getCoordinates(font["glyf"])
    out, s = [], 0
    for e in ends:
        out.append([(x, y, f & 1) for (x, y), f in zip(c[s:e + 1], fl[s:e + 1])])
        s = e + 1
    return out


def rotation(a, b):
    if len(a) != len(b):
        return None
    for k in range(len(a)):
        if b == a[k:] + a[:k]:
            return k
    return None


args = sys.argv[1:]
for sp, bp in zip(args[::2], args[1::2]):
    s, b = TTFont(sp), TTFont(bp)
    cs, cb = s.getBestCmap(), b.getBestCmap()
    rot = Counter()
    closing_dup = 0
    for cp, n in cs.items():
        if cp not in cb:
            continue
        for x, y in zip(contours(s, n), contours(b, cb[cp])):
            r = rotation(x, y)
            rot[r if r is None or r <= 2 else ("len-%d" % (len(x) - r) if len(x) - r <= 2 else "other")] += 1
            if x and x[0] == x[-1]:
                closing_dup += 1
    print("%s vs %s: rotation (positions) -> contours: %s; shipped contours whose first point == last: %d"
          % (sp.split("/")[-1], bp.split("/")[-1], dict(rot), closing_dup))
