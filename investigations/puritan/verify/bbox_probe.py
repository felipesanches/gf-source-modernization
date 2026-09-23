"""Question answered: in each font, which glyphs set the true (point) yMax/yMin,
and where does a glyf header disagree with the glyph's own decomposed points?"""
import sys
from fontTools.ttLib import TTFont
from fontTools.pens.boundsPen import ControlBoundsPen
for p in sys.argv[1:]:
    f = TTFont(p); gs = f.getGlyphSet(); glyf = f['glyf']
    tops = []; stale = []
    for n in f.getGlyphOrder():
        pen = ControlBoundsPen(gs); gs[n].draw(pen)
        if pen.bounds is None: continue
        xmin, ymin, xmax, ymax = pen.bounds
        g = glyf[n]
        tops.append((ymax, n, ymin))
        if g.isComposite() and (g.yMax != ymax or g.yMin != ymin or g.xMin != xmin or g.xMax != xmax):
            stale.append((n, (g.xMin, g.yMin, g.xMax, g.yMax), (xmin, ymin, xmax, ymax)))
    tops.sort(reverse=True)
    h = f['head']
    print(p.split('/')[-3:], 'head y', h.yMin, h.yMax, 'top5', [(t[1], t[0]) for t in tops[:5]],
          'min', min((t[2], t[1]) for t in tops))
    for s in stale: print('   composite header != points:', s)
