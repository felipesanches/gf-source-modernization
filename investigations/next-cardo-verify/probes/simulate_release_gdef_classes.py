"""simulate_release_gdef_classes.py -- SIMULATION on a built font: give our build the
release's GDEF glyph classes (by glyph name), leaving every lookup (and its flags) as
fontc wrote it.

Question: Cardo-Bold's release classes EVERY glyph as a base (FontForge 20110222
gdefclass(): no GlyphClass and no mark anchor in the .sfd -> base), while our build
classes 165 combining marks as marks (babelfont leaves them uncategorised; fontc's
GlyphData makes them marks). Is that GDEF difference alone enough to explain the
kern-across-mark differences the cardo unit attributes to fontc's IgnoreMarks kern
lookup (177/426)? If the release's classes close them with the IgnoreMarks flag still
in place, a converter-fidelity rule (reproduce FontForge's gdefclass) closes Bold
without any fontc change.

Run: $PY simulate_release_gdef_classes.py <release.ttf> <built.ttf> <out.ttf>
Then: $PY ../../next-cardo/probes/shaping_compare.py <release.ttf> <out.ttf> --only pairs,kern+mark,base+mark
"""
import sys
from fontTools.ttLib import TTFont

rel, built, out = sys.argv[1:4]
R, B = TTFont(rel), TTFont(built)
rc = R["GDEF"].table.GlyphClassDef.classDefs
bo = set(B.getGlyphOrder())
bc = B["GDEF"].table.GlyphClassDef.classDefs
before = dict(bc)
bc.clear()
for g, c in rc.items():
    if g in bo:
        bc[g] = c
changed = sum(1 for g in bo if before.get(g, 0) != bc.get(g, 0))
B.save(out)
print("GDEF classes replaced with the release's: %d glyph(s) changed class" % changed)
