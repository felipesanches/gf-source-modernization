"""Question: what GSUB does each Tuffy binary carry? Prints, per font, the
script/langsys -> feature tags, and per feature the lookups with type and a
summary (number of mappings). Usage: gsub_dump.py <font> ..."""
import sys
from fontTools.ttLib import TTFont
for p in sys.argv[1:]:
    f = TTFont(p); print("==", p)
    if "GSUB" not in f: print("  no GSUB"); continue
    t = f["GSUB"].table
    for sr in t.ScriptList.ScriptRecord:
        ls = [("dflt", sr.Script.DefaultLangSys)] + [(l.LangSysTag, l.LangSys) for l in sr.Script.LangSysRecord]
        for tag, l in ls:
            if l is None: continue
            print("  %s/%s: %s" % (sr.ScriptTag, tag, " ".join(sorted(t.FeatureList.FeatureRecord[i].FeatureTag for i in l.FeatureIndex))))
    for fi, fr in enumerate(t.FeatureList.FeatureRecord):
        desc = []
        for li in fr.Feature.LookupListIndex:
            lk = t.LookupList.Lookup[li]; n = 0
            for st in lk.SubTable:
                if lk.LookupType == 7: st = st.ExtSubTable
                if hasattr(st, "mapping"): n += len(st.mapping)
                elif hasattr(st, "ligatures"): n += sum(len(v) for v in st.ligatures.values())
                elif hasattr(st, "alternates"): n += len(st.alternates)
            desc.append("L%d(t%d,n=%d,flag=%d)" % (li, lk.LookupType, n, lk.LookupFlag))
        print("  feat %d %s: %s" % (fi, fr.FeatureTag, " ".join(desc)))
