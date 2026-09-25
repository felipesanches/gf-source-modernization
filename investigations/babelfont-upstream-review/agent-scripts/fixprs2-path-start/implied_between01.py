import sys
from collections import Counter
from fontTools.ttLib import TTFont
import glyphsLib
from glyphsLib.parser import load as gload
rel, built, gpath = sys.argv[1:4]
gf = gload(open(gpath))
starts = {}
for g in gf.glyphs:
    uni = g.unicode
    if not uni: continue
    for l in g.layers:
        if l.layerId != gf.masters[0].id: continue
        starts[int(uni, 16)] = [tuple(p.nodes[-1].position) for p in l.paths if p.closed and p.nodes]
def contours(font, name):
    g = font["glyf"][name]
    if g.isComposite() or g.numberOfContours <= 0: return []
    c, ends, fl = g.getCoordinates(font["glyf"]); out, s = [], 0
    for e in ends:
        out.append([(x, y, f & 1) for (x, y), f in zip(c[s:e + 1], fl[s:e + 1])]); s = e + 1
    return out
s, b = TTFont(rel), TTFont(built)
cs, cb = s.getBestCmap(), b.getBestCmap()
t = Counter()
for cp, n in cs.items():
    if cp not in cb or cp not in starts: continue
    for i, (x, y) in enumerate(zip(contours(s, n), contours(b, cb[cp]))):
        if x[0][:2] == y[0][:2]: continue
        st = starts[cp][i] if i < len(starts[cp]) else None
        m01 = ((x[0][0] + x[1][0]) / 2, (x[0][1] + x[1][1]) / 2)
        mlf = ((x[-1][0] + x[0][0]) / 2, (x[-1][1] + x[0][1]) / 2)
        close = lambda a, q: q is not None and abs(a[0] - q[0]) <= 1 and abs(a[1] - q[1]) <= 1
        t[("source start ~ mid(rel0,rel1)", close(m01, st), "~ mid(rel-1,rel0)", close(mlf, st))] += 1
for k, v in t.most_common(): print(v, k)
