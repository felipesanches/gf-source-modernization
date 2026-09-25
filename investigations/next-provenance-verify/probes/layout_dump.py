#!/usr/bin/env python3
"""What lookups (type, flag, subtable count, rule count, per-feature/script use) and
PfEd lookup names does a font carry?  Used to compare the Thabit releases with a build.

Run: /home/fsanches/compartilhado/gftools/venv/bin/python3 layout_dump.py <font.ttf>...
"""
import sys
from fontTools.ttLib import TTFont


def rules(l):
    n = 0
    for st in l.SubTable:
        if hasattr(st, "ExtSubTable"):
            st = st.ExtSubTable
        if hasattr(st, "ligatures"):
            n += sum(len(v) for v in st.ligatures.values())
        elif hasattr(st, "mapping"):
            n += len(st.mapping)
        elif hasattr(st, "MarkCoverage") and hasattr(st, "BaseCoverage"):
            n += len(st.BaseCoverage.glyphs)
        elif hasattr(st, "LigatureCoverage"):
            n += len(st.LigatureCoverage.glyphs)
        elif hasattr(st, "Mark2Coverage"):
            n += len(st.Mark2Coverage.glyphs)
    return n


for p in sys.argv[1:]:
    f = TTFont(p)
    print("==", p)
    for tag in ("GSUB", "GPOS"):
        if tag not in f:
            print(" ", tag, "absent"); continue
        t = f[tag].table
        use = {}
        for sr in t.ScriptList.ScriptRecord:
            langs = [("dflt", sr.Script.DefaultLangSys)] + [(l.LangSysTag, l.LangSys) for l in sr.Script.LangSysRecord]
            for lt, ls in langs:
                if ls is None: continue
                for fi in ls.FeatureIndex:
                    fr = t.FeatureList.FeatureRecord[fi]
                    for li in fr.Feature.LookupListIndex:
                        use.setdefault(li, set()).add("%s/%s/%s" % (fr.FeatureTag, sr.ScriptTag, lt.strip()))
        for i, l in enumerate(t.LookupList.Lookup if t.LookupList else []):
            print("  %s %d type %d flag %d subtables %d rules/bases %d  %s" % (
                tag, i, l.LookupType, l.LookupFlag, l.SubTableCount, rules(l), sorted(use.get(i, []))))
