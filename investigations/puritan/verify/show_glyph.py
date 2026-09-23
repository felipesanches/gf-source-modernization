import sys
from fontTools.ttLib import TTFont
for p in sys.argv[2:]:
    f = TTFont(p); g = f['glyf'][sys.argv[1]]
    print(p.split('/')[-3:], 'composite' if g.isComposite() else 'simple', 'hdr', getattr(g,'xMin',None), getattr(g,'yMin',None), getattr(g,'xMax',None), getattr(g,'yMax',None))
    if g.isComposite():
        for c in g.components: print('   comp', c.glyphName, c.x, c.y, c.flags)
        continue
    coords, ends, flags = g.getCoordinates(f['glyf'])
    s = 0
    for e in ends:
        print('   ', [(int(x), int(y), 'o' if fl & 1 else 'x') for (x, y), fl in zip(coords[s:e+1], flags[s:e+1])])
        s = e + 1
