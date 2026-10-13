"""Which Unicode general categories does HarfBuzz take for marks in a font without GDEF?
A font without GDEF kerns a a by -100 under IgnoreMarks; shaping a + X + a moves the
second a only if HarfBuzz synthesised X as a mark."""
import io
import uharfbuzz as hb
from fontTools.fontBuilder import FontBuilder
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
from fontTools.pens.ttGlyphPen import TTGlyphPen

tests = {"Mn U+0301": 0x0301, "Me U+20DD": 0x20DD, "Me U+0488": 0x0488, "Mc U+0903": 0x0903,
         "Mn+ignorable U+034F": 0x034F}
order = [".notdef", "a"] + ["g%04X" % cp for cp in tests.values()]
fb = FontBuilder(1000, isTTF=True)
fb.setupGlyphOrder(order)
fb.setupCharacterMap({ord("a"): "a", **{cp: "g%04X" % cp for cp in tests.values()}})
def box():
    p = TTGlyphPen(None); p.moveTo((0, 0)); p.lineTo((0, 100)); p.lineTo((100, 100)); p.lineTo((100, 0)); p.closePath(); return p.glyph()
fb.setupGlyf({n: box() for n in order})
fb.setupHorizontalMetrics({n: (500, 0) for n in order})
fb.setupHorizontalHeader(ascent=800, descent=-200)
fb.setupNameTable({"familyName": "Probe", "styleName": "Regular"})
fb.setupOS2(); fb.setupPost()
addOpenTypeFeaturesFromString(fb.font, "feature kern { lookupflag IgnoreMarks; pos a a -100; } kern;")
if "GDEF" in fb.font:
    del fb.font["GDEF"]
buf = io.BytesIO(); fb.font.save(buf)
font = hb.Font(hb.Face(buf.getvalue()))
for label, cp in tests.items():
    b = hb.Buffer(); b.add_str("a" + chr(cp) + "a"); b.guess_segment_properties()
    hb.shape(font, b, {"kern": True})
    x = sum(p.x_advance for p in b.glyph_positions[:1])
    print("%-22s first a advance %d -> %s" % (label, x, "MARK (kern applied across it)" if x == 400 else "base"))
print("harfbuzz", hb.__version__)
