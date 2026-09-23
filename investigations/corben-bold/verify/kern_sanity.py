# Sanity check for kern_pairs.py: how many pairs does each font actually kern?
import sys, itertools
import uharfbuzz as hb
from fontTools.ttLib import TTFont
for p in sys.argv[1:]:
    t=TTFont(p); f=hb.Font(hb.Face(open(p,"rb").read())); go=t.getGlyphOrder(); hm=t["hmtx"].metrics
    cps=[c for c in sorted(t.getBestCmap()) if c>0x20]
    for feats in ({},{"smcp":True}):
        n=0; ex=None
        for a,b in itertools.product(cps,cps):
            buf=hb.Buffer(); buf.add_str(chr(a)+chr(b)); buf.guess_segment_properties(); hb.shape(f,buf,feats)
            adv=sum(q.x_advance for q in buf.glyph_positions); nat=sum(hm[go[i.codepoint]][0] for i in buf.glyph_infos)
            if adv!=nat:
                n+=1; ex=ex or (chr(a)+chr(b),adv-nat)
        print(p.split("/")[-3] if "baseline" in p else "release", feats, "kerned pairs", n, "e.g.", ex)
