"""Writes noname.ttf, whose post table (format 3) names no glyph: glyph 1 is
encoded (U+0061), glyph 2 is not. fontTools reads them as .notdef, a and
glyph00002: python3 make_noname.py"""
from fontTools.fontBuilder import FontBuilder
from fontTools.ttLib.tables._g_l_y_f import Glyph

order = [".notdef", "a", "extra"]
fb = FontBuilder(1000, isTTF=True)
fb.setupGlyphOrder(order)
fb.setupCharacterMap({ord("a"): "a"})
fb.setupGlyf({name: Glyph() for name in order})
fb.setupHorizontalMetrics({name: (500, 0) for name in order})
fb.setupHorizontalHeader()
fb.setupPost()
fb.font["post"].formatType = 3.0
fb.font["head"].created = fb.font["head"].modified = 0
fb.font.recalcTimestamp = False
fb.save("noname.ttf")
