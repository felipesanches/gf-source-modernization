# Compare glyph sets, advances and decomposed outlines (as point sequences, start-point
# and direction independent via sorted point multiset) between release and build.
import sys
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.boundsPen import BoundsPen
R=TTFont(sys.argv[1]); B=TTFont(sys.argv[2])
rg=set(R.getGlyphOrder()); bg=set(B.getGlyphOrder())
print("release",len(rg),"build",len(bg),"only release",sorted(rg-bg),"only build",sorted(bg-rg))
rs=R.getGlyphSet(); bs=B.getGlyphSet()
adv=[]; pts=[]; bnd=[]
for n in sorted(rg&bg):
    if R["hmtx"][n][0]!=B["hmtx"][n][0]: adv.append((n,R["hmtx"][n][0],B["hmtx"][n][0]))
    def P(gs):
        p=DecomposingRecordingPen(gs); gs[n].draw(p)
        return sorted(tuple(round(c) for pt in args if pt is not None for c in pt) for op,args in p.value if args)
    if P(rs)!=P(bs): pts.append(n)
    a=BoundsPen(rs); rs[n].draw(a); b=BoundsPen(bs); bs[n].draw(b)
    if a.bounds!=b.bounds: bnd.append((n,a.bounds,b.bounds))
print("advance differs",len(adv),adv[:10])
print("point multiset differs",len(pts),pts[:20])
print("bounds differ",len(bnd),bnd[:10])
