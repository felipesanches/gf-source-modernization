#!/usr/bin/env python3
"""Question answered: which fonts of a google/fonts checkout have a post table that gives
one name to more than one glyph, and do those glyphs differ?

Usage: scan.py <google/fonts checkout>
Prints one line per font with a duplicated name: path, name, glyph indices, and each
glyph's (advance, lsb, contours, code points).
"""
import glob
import os
import sys

from fontTools.ttLib import TTFont

root = sys.argv[1]
fonts = sorted(glob.glob(os.path.join(root, "*", "*", "*.ttf")))
hits = 0
for path in fonts:
    try:
        font = TTFont(path, lazy=True)
        order = font.getGlyphOrder()
        stated = getattr(font["post"], "mapping", None) or {}
        indices = {}
        for index, name in enumerate(order):
            indices.setdefault(stated.get(name, name), []).append(index)
        dup = {n: i for n, i in indices.items() if len(i) > 1}
        if not dup:
            continue
        cmap = {}
        for cp, name in (font.getBestCmap() or {}).items():
            cmap.setdefault(name, []).append("U+%04X" % cp)
        hits += 1
        for name, idx in sorted(dup.items()):
            desc = []
            for i in idx:
                g = order[i]
                contours = font["glyf"][g].numberOfContours if "glyf" in font else "?"
                desc.append("%d:%s" % (i, (font["hmtx"][g][0], font["hmtx"][g][1], contours,
                                            ",".join(cmap.get(g, [])))))
            print("%s\t%s\t%s" % (os.path.relpath(path, root), name, " ".join(desc)))
    except Exception as e:  # a font fontTools cannot read is reported, not skipped
        print("%s\tERROR\t%s" % (os.path.relpath(path, root), e))
print("# %d of %d fonts have a duplicated post name" % (hits, len(fonts)))
