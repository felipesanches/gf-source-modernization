#!/usr/bin/env python3
"""Question answered: what must the TTF reader handle to read GPOS pair kerning into the master
kerning (Simon's P7, babelfont#105) for the families on the binary route (families-binary.tsv)?

Per shipped style: the lookups the `kern` feature uses, their types (2 = pair; 8/9 = contextual or
extension), PairPos formats (1 glyph pairs, 2 class pairs), whether the value records touch more
than the first glyph's XAdvance, the lookup flags, whether a contextual lookup also calls them, and
the scripts `kern` is registered for. A style is SIMPLE when every kern lookup is a pair lookup
(directly or through an extension) with first-glyph XAdvance only and no flags beyond IgnoreMarks,
and no contextual lookup calls it.

Usage: python3 -I tools/probes/ttf_gpos_kerning/census.py > tools/probes/ttf_gpos_kerning/census-<date>.tsv
"""
import csv, os, sys
from fontTools.ttLib import TTFont

W = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
GF = "/home/fsanches/compartilhado/google/fonts/"


def subtables(lookup):
    for st in lookup.SubTable:
        yield (st.ExtSubTable, st.ExtensionLookupType) if lookup.LookupType == 9 else (st, lookup.LookupType)


def main():
    rows = list(csv.DictReader(open(os.path.join(W, "families-binary.tsv")), delimiter="\t"))
    print("\t".join(["repo", "style", "kern_lookups", "types", "pair_formats", "beyond_xadvance",
                     "flags", "called_by_contextual", "scripts", "verdict"]))
    for r in rows:
        tt = TTFont(GF + r["shipped"], lazy=True)
        if "GPOS" not in tt or not tt["GPOS"].table.FeatureList:
            print("\t".join([r["repo"], r["style"], "0", "", "", "", "", "", "", "NO-GPOS-KERN"]))
            continue
        g = tt["GPOS"].table
        kern_idx = sorted({i for fr in g.FeatureList.FeatureRecord if fr.FeatureTag == "kern"
                           for i in fr.Feature.LookupListIndex})
        if not kern_idx:
            print("\t".join([r["repo"], r["style"], "0", "", "", "", "", "", "", "NO-GPOS-KERN"]))
            continue
        scripts = sorted({sr.ScriptTag for sr in g.ScriptList.ScriptRecord})
        lookups = g.LookupList.Lookup
        called = set()
        for lk in lookups:
            for st, t in subtables(lk):
                if t in (7, 8):
                    for attr in ("PosLookupRecord", "SubstLookupRecord"):
                        for rec in getattr(st, attr, None) or []:
                            called.add(rec.LookupListIndex)
                    for rs in (getattr(st, "PosRuleSet", None) or []) + (getattr(st, "ChainPosRuleSet", None) or []) + (getattr(st, "PosClassSet", None) or []) + (getattr(st, "ChainPosClassSet", None) or []):
                        if rs is None:
                            continue
                        for rule in (getattr(rs, "PosRule", None) or []) + (getattr(rs, "ChainPosRule", None) or []) + (getattr(rs, "PosClassRule", None) or []) + (getattr(rs, "ChainPosClassRule", None) or []):
                            for rec in rule.PosLookupRecord:
                                called.add(rec.LookupListIndex)
        types, formats, beyond, flags = set(), set(), False, set()
        for i in kern_idx:
            lk = lookups[i]
            flags.add(lk.LookupFlag)
            for st, t in subtables(lk):
                types.add(t)
                if t == 2:
                    formats.add(st.Format)
                    if (st.ValueFormat1 & ~0x0004) or st.ValueFormat2:
                        beyond = True
        cc = bool(called & set(kern_idx))
        simple = types == {2} and not beyond and flags <= {0, 8} and not cc
        print("\t".join([r["repo"], r["style"], str(len(kern_idx)), ",".join(map(str, sorted(types))),
                         ",".join(map(str, sorted(formats))), "yes" if beyond else "no",
                         ",".join(map(str, sorted(flags))), "yes" if cc else "no", ",".join(scripts),
                         "SIMPLE" if simple else "COMPLEX"]))


if __name__ == "__main__":
    sys.exit(main())
