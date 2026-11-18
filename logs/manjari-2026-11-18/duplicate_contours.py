#!/usr/bin/env python3
"""Question answered: which glyphs of a UFO draw the same contour more than once (same points
in the same order, any starting point)?

Usage: duplicate_contours.py <font.ufo>...
Prints: ufo, glyph, contours, duplicated contours; then a count per UFO.
Only the default layer's glyphs are read (Manjari's Thin and Bold link data/ into the
Regular UFO, which ufoLib2.Font.open refuses to follow).
"""
import sys

from fontTools.ufoLib import UFOReader
from ufoLib2.objects import Layer


def key(contour):
    pts = [(p.x, p.y, p.type or "") for p in contour.points]
    return min(tuple(pts[i:] + pts[:i]) for i in range(len(pts))) if pts else ()


for path in sys.argv[1:]:
    layer = Layer.read("public.default", UFOReader(path).getGlyphSet())
    name = path.rstrip("/").rsplit("/", 1)[-1]
    n = 0
    for glyph in sorted(layer, key=lambda g: g.name):
        keys = [key(c) for c in glyph.contours]
        dup = len(keys) - len(set(keys))
        if dup:
            n += 1
            print("%s\t%s\t%d\t%d" % (name, glyph.name, len(keys), dup))
    print("# %s: %d glyph(s) with duplicated contours" % (name, n))
