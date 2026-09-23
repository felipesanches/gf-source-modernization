import sys, itertools, uharfbuzz as hb
from fontTools.ttLib import TTFont
F = [(hb.Font(hb.Face(open(p, "rb").read())), TTFont(p)) for p in sys.argv[1:3]]
cps = sorted(set(F[0][1].getBestCmap()) & set(F[1][1].getBestCmap()))
cps = [c for c in cps if c > 0x20 and c not in (0xA0, 0xAD)]
def sh(f, t, s, ft):
    b = hb.Buffer(); b.add_str(s); b.guess_segment_properties(); hb.shape(f, b, ft)
    go = t.getGlyphOrder()
    return [(go[i.codepoint], p.x_advance, p.x_offset, p.y_offset) for i, p in zip(b.glyph_infos, b.glyph_positions)]
for ft in ({}, {"smcp": True}):
    print(ft, sum(sh(*F[0], chr(a) + chr(b), ft) != sh(*F[1], chr(a) + chr(b), ft)
                  for a, b in itertools.product(cps, cps)))
