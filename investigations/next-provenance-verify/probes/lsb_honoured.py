#!/usr/bin/env python3
"""Do rasterizers place a TrueType glyph by its hmtx lsb (phantom point) or by its glyf
coordinates?  Needed to judge the claim that the Thabit obliques' "release-stale" lsb
(lsb != glyf xMin) is what makes diffenator3 draw Arabic glyphs one unit off.

For each (font, glyph): hmtx lsb, glyf xMin, and the outline's leftmost x as FreeType
(unhinted, NO_SCALE) and HarfBuzz (hb_font draw, which diffenator3's shaper uses) report
it. If FreeType/HarfBuzz report xMin + (lsb - xMin) = lsb, the lsb is honoured.

Run: python3 lsb_honoured.py <font.ttf> <glyph>...
"""
import sys
import freetype
import uharfbuzz as hb
from fontTools.ttLib import TTFont

path, names = sys.argv[1], sys.argv[2:]
tt = TTFont(path, recalcBBoxes=False)
face = freetype.Face(path)
blob = hb.Blob.from_file_path(path); hface = hb.Face(blob); hfont = hb.Font(hface)
order = tt.getGlyphOrder()
for n in names:
    gid = order.index(n)
    lsb = tt["hmtx"][n][1]; xmin = tt["glyf"][n].xMin
    face.load_glyph(gid, freetype.FT_LOAD_NO_SCALE | freetype.FT_LOAD_NO_HINTING)
    ft_left = min(p[0] for p in face.glyph.outline.points) if face.glyph.outline.points else None
    ext = hfont.get_glyph_extents(gid)
    print("%s %s: hmtx lsb %d, glyf xMin %d, FreeType leftmost point %s, HarfBuzz extents x_bearing %s" % (
        path.split("/")[-1], n, lsb, xmin, ft_left, ext.x_bearing if ext else None))
