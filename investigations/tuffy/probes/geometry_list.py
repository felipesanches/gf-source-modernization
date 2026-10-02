#!/usr/bin/env python3
"""Question: which release glyphs does tools/functional_gate.py's geometry test fail, and by
how much? Prints every reachable release glyph whose ink differs from its build counterpart
by more than GEOMETRY_THRESHOLD pixels (FreeType unhinted, 8 units/px, fuzz 64), with its
codepoints, worst first, using the gate's own correspondence, bitmaps and threshold.

Usage: geometry_list.py <shipped.ttf> <built.ttf>
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools"))
import freetype
import functional_gate as fg

A, B = fg.Font(sys.argv[1]), fg.Font(sys.argv[2])
key_a, key_b, ka, kb = fg.correspondence(A, B)
inv_b = {k: n for n, k in kb.items()}
ga, gb = freetype.Face(A.path), freetype.Face(B.path)
ppem = max(8, round(A.upem / fg.GEOMETRY_UNITS_PER_PX))
ga.set_pixel_sizes(0, ppem)
gb.set_pixel_sizes(0, ppem)
rev = {}
for cp, n in A.cmap.items():
    rev.setdefault(n, []).append(cp)
bad = []
for n in sorted(A.reachable()):
    nb = inv_b.get(ka[n])
    if nb is None or A.outline(n) == B.outline(nb):
        continue
    px = fg.bitmap_diff(fg.ft_bitmap(ga, A.gid[n]), fg.ft_bitmap(gb, B.gid[nb]), fg.GEOMETRY_FUZZ)
    if px > fg.GEOMETRY_THRESHOLD:
        bad.append((px, n, nb))
for px, n, nb in sorted(bad, reverse=True):
    print("%6d\t%s\t%s\t%s" % (px, n, nb, " ".join("U+%04X" % c for c in sorted(rev.get(n, [])))))
print("# %d glyph(s) over the threshold" % len(bad), file=sys.stderr)
