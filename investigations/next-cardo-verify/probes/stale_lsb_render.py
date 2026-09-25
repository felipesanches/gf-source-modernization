"""stale_lsb_render.py -- does a stale hmtx left side bearing (hmtx lsb != glyf xMin) move
the rendered glyph under FreeType?

Question: the table gate files every "shipped records <lsb> for an outline at <xMin>"
row as RELEASE-STALE (bookkeeping). TrueType rasterizers place the outline using phantom
point pp1 = xMin - lsb; if FreeType shifts the outline by that amount, a stale lsb is a
RENDERING difference (Cardo-Italic uni0297: lsb 102, xMin 66, 36 units), not bookkeeping.
Loads the glyph unscaled-hinting-off (FT_LOAD_NO_HINTING, and FT_LOAD_NO_SCALE) in both
fonts and prints the outline's xMin relative to the pen origin.

Run: $PY stale_lsb_render.py <release.ttf> <built.ttf> <glyphname> [...]
"""
import sys
import freetype
from fontTools.ttLib import TTFont

rel, built = sys.argv[1:3]
for gname in sys.argv[3:]:
    for label, p in (("release", rel), ("ours", built)):
        tt = TTFont(p)
        gid = tt.getGlyphID(gname)
        g = tt["glyf"][gname]
        lsb = tt["hmtx"][gname][1]
        face = freetype.Face(p)
        res = []
        for flags, fl in ((freetype.FT_LOAD_NO_SCALE, "NO_SCALE"),
                          (freetype.FT_LOAD_NO_HINTING, "NO_HINTING@upem")):
            if fl.startswith("NO_HINTING"):
                face.set_char_size(tt["head"].unitsPerEm * 64)
            face.load_glyph(gid, flags)
            xs = [pt[0] for pt in face.glyph.outline.points]
            scale = 64 if fl.startswith("NO_HINTING") else 1
            res.append("%s outline xMin %.1f" % (fl, min(xs) / scale if xs else float("nan")))
        print("%-10s %-8s hmtx lsb %5d glyf xMin %5d | %s" % (gname, label, lsb, g.xMin, " | ".join(res)))
