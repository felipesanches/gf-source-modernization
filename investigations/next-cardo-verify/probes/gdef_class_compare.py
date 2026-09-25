"""gdef_class_compare.py -- per glyph, which GDEF glyph class does the release give and
which does our build give, and what does the .sfd state (GlyphClass: n, where FontForge's
gdefclass() returns n-1; absent -> FontForge infers mark from a mark anchor, ligature
from a Ligature2 PST, else base)?

Question: where our build's GDEF classes differ from the release, is the difference the
converter departing from the .sfd's explicit GlyphClass, or an inference FontForge did not
make? (cardo verification: Regular ours has 11 ligature-class glyphs, the release none;
Bold ours 163 marks, the release none.)

Run: $PY gdef_class_compare.py <release.ttf> <built.ttf> <source.sfd>
"""
import re
import sys
from collections import Counter
from fontTools.ttLib import TTFont

rel, ours, sfd = sys.argv[1:4]
def classes(p):
    f = TTFont(p)
    cd = f["GDEF"].table.GlyphClassDef.classDefs if "GDEF" in f and f["GDEF"].table.GlyphClassDef else {}
    return cd, f.getGlyphOrder(), f["hmtx"].metrics
rc, ro, rh = classes(rel)
oc, oo, oh = classes(ours)
text = open(sfd, encoding="latin-1").read()
src = {}
for m in re.finditer(r"^StartChar: (\S+)\n(.*?)^EndChar", text, re.M | re.S):
    body = m.group(2)
    gc = re.search(r"^GlyphClass: (\d+)", body, re.M)
    src[m.group(1)] = dict(
        glyphclass=int(gc.group(1)) if gc else None,
        anchors=len(re.findall(r"^AnchorPoint:", body, re.M)),
        mark_anchor=bool(re.search(r'^AnchorPoint: "[^"]*" \S+ \S+ (mark|basemark)', body, re.M)),
        lig=bool(re.search(r"^Ligature2:", body, re.M)),
        width=int(re.search(r"^Width: (-?\d+)", body, re.M).group(1)) if re.search(r"^Width:", body, re.M) else None)
pairs = Counter()
examples = {}
for g in set(ro) | set(oo):
    a, b = rc.get(g, 0), oc.get(g, 0)
    if a != b:
        s = src.get(g, {})
        key = (a, b, s.get("glyphclass"), s.get("mark_anchor"), s.get("lig"))
        pairs[key] += 1
        examples.setdefault(key, []).append(g)
print("release classes", dict(Counter(rc.values())), "ours", dict(Counter(oc.values())))
print("(release class, our class, sfd GlyphClass, sfd has mark anchor, sfd has Ligature2): count  examples")
for k, n in sorted(pairs.items(), key=lambda kv: -kv[1]):
    print(k, n, sorted(examples[k])[:12])
