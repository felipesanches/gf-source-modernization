"""Writes aalt.ttf from aalt.fea (feaLib accepts lookup references in aalt):
python3 make_aalt.py"""
from fontTools.feaLib.builder import addOpenTypeFeatures
from fontTools.fontBuilder import FontBuilder
from fontTools.ttLib.tables._g_l_y_f import Glyph

order = [".notdef", "a", "a.alt1", "b", "b.alt1", "b.alt2"]
fb = FontBuilder(1000, isTTF=True)
fb.setupGlyphOrder(order)
fb.setupCharacterMap({ord("a"): "a", ord("b"): "b"})
fb.setupGlyf({name: Glyph() for name in order})
fb.setupHorizontalMetrics({name: (500, 0) for name in order})
fb.setupHorizontalHeader()
fb.setupPost()
addOpenTypeFeatures(fb.font, "aalt.fea")
fb.font["head"].created = fb.font["head"].modified = 0
fb.font.recalcTimestamp = False
fb.save("aalt.ttf")
