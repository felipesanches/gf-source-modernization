#!/usr/bin/env python3
"""Could the release's TrueType instructions run unchanged on our build?

Usage: points.py <shipped.ttf> <built.ttf>
Glyph programs address points by index, so they carry over only to a glyph with the
same points in the same order. Per glyph (paired by name) this compares the contour
end points, every point's coordinates and on-curve flag, and for a composite its
components (name, offset, and the flags that change what instructions see). Prints
  <identical> of <shipped glyphs> point-identical, <n> with instructions among the rest
and lists up to 10 differing glyphs with the first difference.
"""
import sys
from fontTools.ttLib import TTFont

COMPONENT_FLAGS = 0x0002 | 0x0004 | 0x0200 | 0x0400 | 0x0800   # ARGS_ARE_XY, ROUND_XY, USE_MY_METRICS, SCALED/UNSCALED offset

def shape(font, name):
    g = font["glyf"][name]
    if g.isComposite():
        return ("composite", tuple((c.glyphName, getattr(c, "x", None), getattr(c, "y", None),
                                    c.flags & COMPONENT_FLAGS,
                                    getattr(c, "firstPt", None), getattr(c, "secondPt", None),
                                    getattr(c, "transform", None) and tuple(map(tuple, c.transform)))
                                   for c in g.components))
    if not g.numberOfContours:
        return ("empty",)
    return ("simple", tuple(g.endPtsOfContours), tuple(g.coordinates), tuple(f & 1 for f in g.flags))

def has_code(font, name):
    g = font["glyf"][name]
    return bool(hasattr(g, "program") and g.program and len(g.program.getBytecode()))

def first_difference(a, b):
    if a[0] != b[0]:
        return "%s vs %s" % (a[0], b[0])
    if a[0] == "simple":
        if a[1] != b[1]:
            return "contour ends %s vs %s" % (a[1][:6], b[1][:6])
        for i, (p, q) in enumerate(zip(a[2], b[2])):
            if p != q:
                return "point %d %s vs %s" % (i, p, q)
        return "on-curve flags"
    return "components %s vs %s" % (a[1][:2], b[1][:2])

def main(shipped, built):
    s, b = TTFont(shipped), TTFont(built)
    names = [n for n in s.getGlyphOrder()]
    same, differing, coded_differing, missing = 0, [], 0, 0
    for n in names:
        if n not in b["glyf"].glyphs:
            missing += 1
            continue
        a, c = shape(s, n), shape(b, n)
        if a == c:
            same += 1
        else:
            differing.append((n, first_difference(a, c)))
            coded_differing += has_code(s, n)
    print("%d of %d point-identical, %d differ (%d of them instructed), %d missing by name; glyph order %s"
          % (same, len(names), len(differing), coded_differing, missing,
             "same" if s.getGlyphOrder() == b.getGlyphOrder() else "differs"))
    for n, why in differing[:10]:
        print("  %s: %s" % (n, why))

if __name__ == "__main__":
    main(*sys.argv[1:3])
