import sys
from collections import Counter
from fontTools.ttLib import TTFont
def contours(font, name):
    g = font["glyf"][name]
    if g.isComposite() or g.numberOfContours <= 0:
        return []
    c, ends, fl = g.getCoordinates(font["glyf"])
    out, s = [], 0
    for e in ends:
        out.append([(x, y, f & 1) for (x, y), f in zip(c[s:e + 1], fl[s:e + 1])])
        s = e + 1
    return out
s, b = TTFont(sys.argv[1]), TTFont(sys.argv[2])
cs, cb = s.getBestCmap(), b.getBestCmap()
t = Counter()
for cp, n in cs.items():
    if cp not in cb: continue
    for x, y in zip(contours(s, n), contours(b, cb[cp])):
        if x[0][:2] == y[0][:2]: continue
        k = "rel[0] %s rel[1] %s rel[-1] %s; built[0]==rel[1]: %s; built[0]==rel[-1]: %s" % (
            "on" if x[0][2] else "off", "on" if x[1][2] else "off", "on" if x[-1][2] else "off",
            y[0][:2] == x[1][:2], y[0][:2] == x[-1][:2])
        t[k] += 1
for k, v in t.most_common(): print(v, k)
