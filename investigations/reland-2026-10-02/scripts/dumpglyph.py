#!/usr/bin/env python3
"""Print a glyph's contours (points, on/off flag), hmtx and header xMin from each font given.
usage: dumpglyph.py <glyph> <font.ttf>...   (glyph name, or U+XXXX)"""
import sys
from fontTools.ttLib import TTFont
name = sys.argv[1]
for p in sys.argv[2:]:
    f = TTFont(p); n = name
    if n.startswith("U+"):
        n = f.getBestCmap()[int(n[2:], 16)]
    g = f["glyf"][n]
    print("==", p.split("/")[-1], n, "hmtx", f["hmtx"][n], "xMin", getattr(g, "xMin", None), "composite" if g.isComposite() else "")
    if g.isComposite():
        for c in g.components: print("   comp", c.glyphName, c.x, c.y, getattr(c, "transform", None), hex(c.flags))
    c, e, fl = g.getCoordinates(f["glyf"]); s = 0
    for end in e:
        print("  ", [(int(c[i][0]), int(c[i][1])) if fl[i] & 1 else ("o", int(c[i][0]), int(c[i][1])) for i in range(s, end + 1)]); s = end + 1
