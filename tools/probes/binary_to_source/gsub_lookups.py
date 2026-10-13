"""Question: how do the GSUB lookup lists of a release and its build line up (type, flags,
nested lookups of chained-context rules, feature -> lookup indices)?
  python3 gsub_lookups.py <release.ttf> <build.ttf>"""
import sys
from fontTools.ttLib import TTFont

def kind(l):
    t, st = l.LookupType, l.SubTable[0]
    if t == 7:
        st = st.ExtSubTable; t = st.LookupType
    extra = ""
    if t == 6:
        if st.Format == 3:
            extra = " nested=%s" % [(r.SequenceIndex, r.LookupListIndex) for r in st.SubstLookupRecord]
        elif st.Format == 2:
            extra = " fmt2 nested=%s" % sorted({(r.SequenceIndex, r.LookupListIndex) for s in st.ChainSubClassSet or [] if s for rule in s.ChainSubClassRule for r in rule.SubstLookupRecord})
        else:
            extra = " fmt1 nested=%s" % sorted({(r.SequenceIndex, r.LookupListIndex) for s in st.ChainSubRuleSet or [] if s for rule in s.ChainSubRule for r in rule.SubstLookupRecord})
    return "type %d x%d flag %d%s" % (t, l.SubTableCount, l.LookupFlag, extra)

for p in sys.argv[1:]:
    f = TTFont(p)
    ll = f["GSUB"].table.LookupList.Lookup
    print(p, len(ll), "lookups")
    for i, l in enumerate(ll):
        print("  %3d %s" % (i, kind(l)))
    for fr in f["GSUB"].table.FeatureList.FeatureRecord:
        print("  feature", fr.FeatureTag, fr.Feature.LookupListIndex)
