# Question: does our build kern every encoded pair the way the release does?
# Shapes every ordered pair of encoded codepoints with HarfBuzz (default features,
# and again with smcp on) through both fonts and compares total advances / offsets.
import sys, itertools
import uharfbuzz as hb
from fontTools.ttLib import TTFont
def load(p):
    b=open(p,"rb").read(); face=hb.Face(b); return hb.Font(face), TTFont(p)
rel, relt = load(sys.argv[1]); ours, ourt = load(sys.argv[2])
cps=sorted(set(relt.getBestCmap())&set(ourt.getBestCmap()))
cps=[c for c in cps if c>0x20 and c not in (0xA0,0xAD)]
def shape(f, s, feats):
    buf=hb.Buffer(); buf.add_str(s); buf.guess_segment_properties()
    hb.shape(f, buf, feats)
    return tuple((i.codepoint, p.x_advance, p.x_offset, p.y_offset) for i,p in zip(buf.glyph_infos, buf.glyph_positions))
relgo=relt.getGlyphOrder(); ourgo=ourt.getGlyphOrder()
for feats,label in (({},"default"),({"smcp":True},"smcp")):
    nd=0; ex=[]
    nk_rel=nk_ours=0
    for a,b in itertools.product(cps,cps):
        s=chr(a)+chr(b)
        r=shape(rel,s,feats); o=shape(ours,s,feats)
        rn=[(relgo[g],adv,xo,yo) for g,adv,xo,yo in r]; on=[(ourgo[g],adv,xo,yo) for g,adv,xo,yo in o]
        if rn!=on:
            nd+=1
            if len(ex)<15: ex.append((hex(a),hex(b),rn,on))
    print(label, "pairs", len(cps)**2, "differ", nd)
    for e in ex: print("  ",e)
