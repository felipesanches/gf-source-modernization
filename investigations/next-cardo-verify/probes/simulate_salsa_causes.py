"""simulate_salsa_causes.py -- SIMULATIONS on a built font whose release has a GDEF that
classes every glyph base while our build has NO GDEF at all (landed Salsa-Regular).

Question: the cardo unit lists Salsa-Regular (landed CLEAN) among the styles whose
kern-across-mark differences need fontc's KernFeatureWriter ignoreMarks=false. Our
landed Salsa carries no GDEF, so HarfBuzz synthesises glyph classes from Unicode:
combining marks become marks, which (1) an IgnoreMarks kern lookup skips and (2)
HarfBuzz zero-widths at shaping even though hmtx gives them 334. Which fix closes what?
  flag0     kern lookups' IgnoreMarks/UseMarkFilteringSet cleared (the unit's fontc idea)
  relgdef   the release's GDEF table copied into our build (FontForge's classes)
Writes <out-prefix>-flag0.ttf and <out-prefix>-relgdef.ttf.

Run: $PY simulate_salsa_causes.py <release.ttf> <built.ttf> <out-prefix>
Then shape each with next-cardo/probes/shaping_compare.py --only pairs,kern+mark,base+mark
"""
import copy
import sys
from fontTools.ttLib import TTFont

rel, built, pre = sys.argv[1:4]
f = TTFont(built)
kern = set()
for fr in f["GPOS"].table.FeatureList.FeatureRecord:
    if fr.FeatureTag == "kern":
        kern.update(fr.Feature.LookupListIndex)
for i in kern:
    lk = f["GPOS"].table.LookupList.Lookup[i]
    lk.LookupFlag &= ~0x18
    if hasattr(lk, "MarkFilteringSet"):
        del lk.MarkFilteringSet
f.save(pre + "-flag0.ttf")
g = TTFont(built)
r = TTFont(rel)
g["GDEF"] = copy.deepcopy(r["GDEF"])
assert g.getGlyphOrder() == r.getGlyphOrder() or all(n in set(g.getGlyphOrder()) for n in r["GDEF"].table.GlyphClassDef.classDefs)
g.save(pre + "-relgdef.ttf")
print("wrote", pre + "-flag0.ttf", pre + "-relgdef.ttf")
