# Compare outlines as multisets of undirected explicit segments (implied on-curve points
# made explicit by BasePen), after decomposing composites. Glyph drawn via the raw glyf
# coordinates (no lsb phantom shift), so a stale hmtx lsb does not show as a difference.
import sys
from collections import Counter
from fontTools.ttLib import TTFont
from fontTools.pens.basePen import BasePen, DecomposingPen
class Seg(BasePen):
    skipMissingComponents=True
    def __init__(s,gs): BasePen.__init__(s,gs); s.segs=Counter()
    def r(s,p): return (round(p[0]*2)/2, round(p[1]*2)/2)
    def _moveTo(s,p): s.cur=s.r(p); s.start=s.cur
    def _lineTo(s,p):
        q=s.r(p); s.segs[tuple(sorted([s.cur,q]))]+=1; s.cur=q
    def _qCurveToOne(s,p1,p2):
        a,b,c=s.cur,s.r(p1),s.r(p2); s.segs[tuple([min(a,c),b,max(a,c)])]+=1; s.cur=c
    def _curveToOne(s,p1,p2,p3):
        a,b,c,d=s.cur,s.r(p1),s.r(p2),s.r(p3); k=(a,b,c,d) if a<=d else (d,c,b,a); s.segs[k]+=1; s.cur=d
    def _closePath(s):
        if s.cur!=s.start: s.segs[tuple(sorted([s.cur,s.start]))]+=1
    def _endPath(s): pass
def raw(font):
    glyf=font["glyf"]
    class GS(dict):
        def __missing__(self,n):
            g=glyf[n]
            class W:
                def draw(_,pen): g.draw(pen, glyf)
            return W()
    return GS()
R=TTFont(sys.argv[1]); B=TTFont(sys.argv[2])
rs,bs=raw(R),raw(B)
diff=[]
for n in sorted(set(R.getGlyphOrder())&set(B.getGlyphOrder())):
    a=Seg(rs); rs[n].draw(a); b=Seg(bs); bs[n].draw(b)
    if a.segs!=b.segs: diff.append((n,sum(a.segs.values()),sum(b.segs.values())))
print("glyphs compared",len(set(R.getGlyphOrder())&set(B.getGlyphOrder())),"outline differs",len(diff),diff[:15])
