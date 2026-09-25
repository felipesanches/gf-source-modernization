"""layout_summary.py -- what GSUB/GPOS lookups (type, flag, mark filtering set) and
features does each font carry, in LookupList order?

Question: do two fonts (e.g. the Cardo release and our build) hold the same lookups,
in the same order, with the same flags? Used to check the cardo unit's claims about
kern lookup flags (release 0 vs ours IgnoreMarks) and lookup order.

Run: $PY layout_summary.py <font.ttf> [<font.ttf> ...]
"""
import sys
from fontTools.ttLib import TTFont

for path in sys.argv[1:]:
    f = TTFont(path)
    print("==", path)
    gdef = f["GDEF"].table if "GDEF" in f else None
    if gdef is not None:
        cd = gdef.GlyphClassDef.classDefs if gdef.GlyphClassDef else {}
        from collections import Counter
        print("  GDEF classes", dict(Counter(cd.values())),
              "MarkGlyphSetsDef", bool(getattr(gdef, "MarkGlyphSetsDef", None)),
              "LigCaretList", gdef.LigCaretList.LigGlyphCount if gdef.LigCaretList else 0)
    for tag in ("GSUB", "GPOS"):
        if tag not in f:
            print(" ", tag, "absent"); continue
        t = f[tag].table
        feats = {}
        if t.FeatureList:
            for i, fr in enumerate(t.FeatureList.FeatureRecord):
                for li in fr.Feature.LookupListIndex:
                    feats.setdefault(li, set()).add(fr.FeatureTag)
        lk = t.LookupList.Lookup if t.LookupList else []
        print(" ", tag, len(lk), "lookups")
        for i, l in enumerate(lk):
            st = l.SubTable[0]
            lt = l.LookupType
            if lt in (7, 9) and hasattr(st, "ExtSubTable"):
                lt = st.ExtensionLookupType
            print(f"    {i:3d} type {lt} flag {l.LookupFlag:#06x} mfs {getattr(l,'MarkFilteringSet',None)} subtables {l.SubTableCount} feats {sorted(feats.get(i, []))}")
