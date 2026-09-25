#!/usr/bin/env python3
"""What exactly differs between two fonts' GSUB tables (lookup order, lookups, subtables,
script/language registrations)?

Question: the table gate reports GSUB.script_list / feature_list / lookup_list as one
truncated JSON line. This prints both fonts' GSUB in a canonical, human-diffable text
form so the difference can be named precisely:

  * SCRIPTS: every script/language system, its required feature and its feature list
    as (index:tag) pairs, then the lookups those features reach, in lookup-list order.
  * FEATURES: index, tag, lookup indices.
  * LOOKUPS: index, type (extension unwrapped), flag, subtable count, and one line per
    subtable with its rules. Glyphs are printed by NAME; mapped glyphs also carry their
    codepoint (e.g. `zero[U+0030]`) so a rename between the fonts is visible as such.
    Chaining/contextual subtables print format, coverages / class defs and the nested
    lookup records.

Run:
    /home/fsanches/compartilhado/gftools/venv/bin/python3 gsub_dump.py <font.ttf> [TAG]
TAG defaults to GSUB; GPOS prints only scripts/features/lookup headers.
Output goes to stdout; the investigation keeps one file per font under runs/dump/.
"""
import sys

from fontTools.ttLib import TTFont


def main():
    path = sys.argv[1]
    tag = sys.argv[2] if len(sys.argv) > 2 else "GSUB"
    f = TTFont(path)
    rev = {}
    for cp, n in sorted(f.getBestCmap().items()):
        rev.setdefault(n, cp)

    def g(n):
        return "%s[U+%04X]" % (n, rev[n]) if n in rev else n

    def gl(names):
        return " ".join(g(n) for n in names)

    if tag not in f:
        print("%s: no %s table" % (path, tag))
        return
    t = f[tag].table
    feats = t.FeatureList.FeatureRecord if t.FeatureList else []
    lookups = t.LookupList.Lookup if t.LookupList else []
    print("# %s %s: %d scripts, %d features, %d lookups" % (
        path.split("/")[-1], tag,
        len(t.ScriptList.ScriptRecord) if t.ScriptList else 0, len(feats), len(lookups)))
    print("## SCRIPTS")
    for sr in (t.ScriptList.ScriptRecord if t.ScriptList else []):
        langs = []
        if sr.Script.DefaultLangSys:
            langs.append(("dflt", sr.Script.DefaultLangSys))
        for lr in sr.Script.LangSysRecord:
            langs.append((lr.LangSysTag.strip(), lr.LangSys))
        for lt, ls in langs:
            fi = list(ls.FeatureIndex)
            req = ls.ReqFeatureIndex
            reached = sorted({li for i in fi for li in feats[i].Feature.LookupListIndex})
            print("%s/%s req=%s feats=[%s] lookups=%s" % (
                sr.ScriptTag, lt, "-" if req == 0xFFFF else req,
                " ".join("%d:%s" % (i, feats[i].FeatureTag) for i in fi), reached))
    print("## FEATURES")
    for i, fr in enumerate(feats):
        print("%d %s %s" % (i, fr.FeatureTag, list(fr.Feature.LookupListIndex)))
    print("## LOOKUPS")
    for i, lk in enumerate(lookups):
        typ = lk.LookupType
        sts = list(lk.SubTable)
        if typ == 7:
            typ = sts[0].ExtensionLookupType
            sts = [s.ExtSubTable for s in sts]
        print("L%d type=%d flag=0x%X subtables=%d" % (i, typ, lk.LookupFlag, len(sts)))
        if tag != "GSUB":
            continue
        for j, st in enumerate(sts):
            fmt = getattr(st, "Format", None)
            if typ == 1:
                print("  st%d single %s" % (j, " ".join(
                    "%s>%s" % (g(k), g(v)) for k, v in st.mapping.items())))
            elif typ == 3:
                print("  st%d alt %s" % (j, " ".join(
                    "%s>{%s}" % (g(k), gl(v)) for k, v in st.alternates.items())))
            elif typ == 4:
                items = []
                for k, ligs in st.ligatures.items():
                    for lig in ligs:
                        items.append("%s+%s>%s" % (g(k), "+".join(g(c) for c in lig.Component),
                                                   g(lig.LigGlyph)))
                print("  st%d lig %s" % (j, " ".join(items)))
            elif typ == 2:
                print("  st%d mult %s" % (j, " ".join(
                    "%s>%s" % (g(k), "+".join(g(x) for x in v)) for k, v in st.mapping.items())))
            elif typ in (5, 6):
                kind = "chain" if typ == 6 else "ctx"
                if fmt == 3:
                    parts = []
                    for a in ("BacktrackCoverage", "InputCoverage", "LookAheadCoverage", "Coverage"):
                        cs = getattr(st, a, None)
                        if cs is None:
                            continue
                        if not isinstance(cs, list):
                            cs = [cs]
                        parts.append("%s=%s" % (a.replace("Coverage", "") or "Cov",
                                                ["[%s]" % gl(c.glyphs) for c in cs]))
                    recs = getattr(st, "SubstLookupRecord", None) or []
                    parts.append("apply=%s" % [(r.SequenceIndex, r.LookupListIndex) for r in recs])
                    print("  st%d %s fmt3 %s" % (j, kind, " ".join(parts)))
                elif fmt == 2:
                    def cd(c):
                        if c is None:
                            return {}
                        out = {}
                        for n, k in c.classDefs.items():
                            out.setdefault(k, []).append(n)
                        return {k: gl(sorted(v)) for k, v in sorted(out.items())}
                    print("  st%d %s fmt2 cov=[%s] back=%s in=%s ahead=%s" % (
                        j, kind, gl(st.Coverage.glyphs),
                        cd(getattr(st, "BacktrackClassDef", None)),
                        cd(getattr(st, "InputClassDef", None) or getattr(st, "ClassDef", None)),
                        cd(getattr(st, "LookAheadClassDef", None))))
                    sets = getattr(st, "ChainSubClassSet", None) or getattr(st, "SubClassSet", None) or []
                    for ci, cs in enumerate(sets):
                        if cs is None:
                            continue
                        rules = getattr(cs, "ChainSubClassRule", None) or getattr(cs, "SubClassRule", None) or []
                        for r in rules:
                            print("     class%d: back=%s in=%s ahead=%s apply=%s" % (
                                ci, list(getattr(r, "Backtrack", [])), list(getattr(r, "Input", None) or getattr(r, "Class", [])),
                                list(getattr(r, "LookAhead", [])),
                                [(x.SequenceIndex, x.LookupListIndex) for x in r.SubstLookupRecord]))
                elif fmt == 1:
                    cov = st.Coverage.glyphs
                    sets = getattr(st, "ChainSubRuleSet", None) or getattr(st, "SubRuleSet", None) or []
                    for gi, rs in enumerate(sets):
                        rules = getattr(rs, "ChainSubRule", None) or getattr(rs, "SubRule", None) or []
                        for r in rules:
                            print("  st%d %s fmt1 first=%s back=[%s] in=[%s] ahead=[%s] apply=%s" % (
                                j, kind, g(cov[gi]), gl(getattr(r, "Backtrack", [])), gl(getattr(r, "Input", [])),
                                gl(getattr(r, "LookAhead", [])),
                                [(x.SequenceIndex, x.LookupListIndex) for x in r.SubstLookupRecord]))
            else:
                print("  st%d type %d fmt %s" % (j, typ, fmt))


if __name__ == "__main__":
    main()
