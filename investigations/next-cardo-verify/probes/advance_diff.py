"""advance_diff.py -- every glyph whose ADVANCE differs between the release and our build,
read straight from both hmtx tables (paired by glyph name, with --rename old=new for a
documented rename), with each glyph's GDEF class on both sides and its .sfd GlyphClass
and Width.

Question: independent of the table gate (which can hide an hmtx width under an lsb
arbitration or behind diffenator3's 'check manually' overflow), which advances differ?
Used to verify the cardo unit's hidden-advance claims (Regular uni0304 / uni05B105BD,
Italic uni2E11 / uniF15B).

Run: $PY advance_diff.py <release.ttf> <built.ttf> <source.sfd> [--rename old=new ...]
"""
import re
import sys
from fontTools.ttLib import TTFont

args = sys.argv[1:]
ren = {}
while "--rename" in args:
    i = args.index("--rename"); o, n = args[i + 1].split("="); ren[o] = n; del args[i:i + 2]
rel, ours, sfd = args[:3]
R, O = TTFont(rel), TTFont(ours)
def cls(f):
    return f["GDEF"].table.GlyphClassDef.classDefs if "GDEF" in f and f["GDEF"].table.GlyphClassDef else {}
rc, oc = cls(R), cls(O)
text = open(sfd, encoding="latin-1").read()
src = {}
for m in re.finditer(r"^StartChar: (\S+)\n(.*?)^EndChar", text, re.M | re.S):
    b = m.group(2)
    gc = re.search(r"^GlyphClass: (\d+)", b, re.M)
    w = re.search(r"^Width: (-?\d+)", b, re.M)
    src[m.group(1)] = (int(gc.group(1)) if gc else None, int(w.group(1)) if w else None,
                       len(re.findall(r"^AnchorPoint:", b, re.M)))
rm, om = R["hmtx"].metrics, O["hmtx"].metrics
n = 0
for g, (aw, _) in rm.items():
    g2 = ren.get(g, g)
    if g2 not in om:
        print("MISSING in ours:", g); continue
    if om[g2][0] != aw:
        n += 1
        print("%-20s release %5d ours %5d  GDEF release %s ours %s  sfd GlyphClass/Width/anchors %s"
              % (g, aw, om[g2][0], rc.get(g, 0), oc.get(g2, 0), src.get(g2, src.get(g))))
print("advance differences:", n, "of", len(rm))
