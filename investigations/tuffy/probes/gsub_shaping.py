"""Question: do the GSUB differences between the v1.272 release and our build
change what users see? Shapes probe strings (every ligature/substitution input
either font declares) with HarfBuzz at DEFAULT features, and with frac/dlig/
sups/ordn/aalt/hlig on, per script/language, through three fonts, and prints
each run where the glyph sequences differ. Glyphs are compared by outline key
(advance + bbox of the resolved glyph), since the fonts name glyphs differently.
Usage: gsub_shaping.py release.ttf ff_export.ttf ours.ttf"""
import sys
import uharfbuzz as hb
from fontTools.ttLib import TTFont
from fontTools.pens.boundsPen import BoundsPen
paths = sys.argv[1:4]
fonts = [TTFont(p) for p in paths]
faces = [hb.Font(hb.Face(open(p, "rb").read())) for p in paths]
keys = []
for f in fonts:
    gs = f.getGlyphSet(); order = f.getGlyphOrder(); k = {}
    for gid, n in enumerate(order):
        bp = BoundsPen(gs); gs[n].draw(bp)
        k[gid] = (f["hmtx"][n][0], tuple(round(v) for v in bp.bounds) if bp.bounds else None)
    keys.append(k)
probes = ["f\u00ed", "f\u00ec", "f\u00ee", "f\u00ef", "ff\u00ed", "ff\u00ef", "gy", "ty", "ct", "st", "\u017ft",
          "1/2", "3/4", "1/8", "1/3", "2/3", "5/8", "1\u20442", "3\u20444", "1a", "2o", "No", "1 2 3 4",
          "\u0162\u0163\u015e\u015f", "a", "A", "O", "\u1fbf\u1fc0"]
setups = [("latn", None, ""), ("latn", "ROM", ""), ("latn", "MOL", ""), ("latn", "CAT", ""), ("latn", "HUN", ""),
          ("grek", None, ""), ("latn", None, "frac"), ("latn", None, "dlig"), ("latn", None, "sups"),
          ("latn", None, "ordn"), ("latn", None, "hlig"), ("grek", None, "ccmp")]
def shape(i, text, script, lang, feat):
    buf = hb.Buffer(); buf.add_str(text); buf.guess_segment_properties()
    buf.script = script
    if lang: buf.language = {"ROM": "ro", "MOL": "mo", "CAT": "ca", "HUN": "hu"}[lang]
    hb.shape(faces[i], buf, {feat: True} if feat else {})
    return [keys[i][g.codepoint] for g in buf.glyph_infos]
n = diff_ro = diff_fo = 0
for script, lang, feat in setups:
    for t in probes:
        r, f, o = (shape(i, t, script, lang, feat) for i in range(3))
        n += 1
        if r != o or f != o:
            diff_ro += r != o; diff_fo += f != o
            print("%-4s %-4s %-5s %-10r release %d glyph(s)%s | ff-export %s | ours %d glyph(s)" % (
                script, lang or "dflt", feat or "-", t, len(r), "" if r == o else " DIFFERS", "same" if f == o else "DIFFERS", len(o)))
print("runs %d: release differs from ours in %d; FontForge's 001.271 export differs from ours in %d" % (n, diff_ro, diff_fo))
