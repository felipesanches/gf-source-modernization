#!/usr/bin/env python3
"""For the Thabit obliques' worst Arabic rendering diffs, are the glyf points of the
release and of our build identical, and is the only difference the release's lsb
(hmtx lsb != glyf xMin, i.e. FreeType shifts the outline by lsb - xMin)?

Run: python3 oblique_glyph_compare.py <release.ttf> <built.ttf> <glyph>...
Prints per glyph: point count, identical coordinates?, max |dx|,|dy|, release (lsb,xMin,shift),
ours (lsb,xMin,shift), advance both.
"""
import sys
from fontTools.ttLib import TTFont

r = TTFont(sys.argv[1], recalcBBoxes=False); b = TTFont(sys.argv[2], recalcBBoxes=False)
for n in sys.argv[3:]:
    gr, gb = r["glyf"][n], b["glyf"][n]
    cr = list(gr.getCoordinates(r["glyf"])[0]); cb = list(gb.getCoordinates(b["glyf"])[0])
    same = cr == cb
    md = max((abs(x1 - x2), abs(y1 - y2)) for (x1, y1), (x2, y2) in zip(cr, cb)) if len(cr) == len(cb) else None
    print("%s: points %d/%d identical=%s maxdelta=%s | release lsb %d xMin %d shift %+d | ours lsb %d xMin %d shift %+d | adv %d/%d" % (
        n, len(cr), len(cb), same, md, r["hmtx"][n][1], gr.xMin, r["hmtx"][n][1] - gr.xMin,
        b["hmtx"][n][1], gb.xMin, b["hmtx"][n][1] - gb.xMin, r["hmtx"][n][0], b["hmtx"][n][0]))
