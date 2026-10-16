"""Writes dupnames.ttf, whose post table names glyphs 2 and 3 both "dupe" (a post
table may; fontTools reads the second as dupe.1): python3 make_dupnames.py"""
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
from fontTools.fontBuilder import FontBuilder
from fontTools.ttLib.tables._g_l_y_f import Glyph

order = [".notdef", "a", "dupa", "dupb"]
fb = FontBuilder(1000, isTTF=True)
fb.setupGlyphOrder(order)
fb.setupCharacterMap({ord("a"): "a"})
fb.setupGlyf({name: Glyph() for name in order})
fb.setupHorizontalMetrics({name: (500, 0) for name in order})
fb.setupHorizontalHeader()
fb.setupPost()
addOpenTypeFeaturesFromString(fb.font, "feature salt { sub a by dupb; } salt;")
fb.font["head"].created = fb.font["head"].modified = 0
fb.font.recalcTimestamp = False
fb.save("dupnames.ttf")
data = open("dupnames.ttf", "rb").read()
# both names become "dupe": the same length, so nothing in the post table moves
assert data.count(b"\x04dupa") == 1 and data.count(b"\x04dupb") == 1
data = data.replace(b"\x04dupa", b"\x04dupe").replace(b"\x04dupb", b"\x04dupe")
open("dupnames.ttf", "wb").write(data)
