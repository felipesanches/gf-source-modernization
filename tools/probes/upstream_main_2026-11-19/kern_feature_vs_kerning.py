#!/usr/bin/env python3
"""Question answered: a VFB's own `kern` feature names FontLab kerning classes that babelfont main
now writes as kerning groups. Does that feature hold anything the converted kerning does not,
and which of the two holds the release's kerning?

Both are expanded to glyph pairs (a group or class to its members, by the groups the .glyphs
states; a more specific pair overrides a class pair) and compared with the release's GPOS `kern`
pair adjustments (format 1 and 2, nonzero x advance).

Usage: kern_feature_vs_kerning.py <converted .glyphs> <release .ttf>
"""
import collections
import re
import sys

import glyphsLib
from fontTools.ttLib import TTFont


def release_pairs(path):
    t = TTFont(path)
    gpos = t["GPOS"].table
    out = {}
    for li in [i for fr in gpos.FeatureList.FeatureRecord if fr.FeatureTag == "kern"
               for i in fr.Feature.LookupListIndex]:
        for st in gpos.LookupList.Lookup[li].SubTable:
            st = getattr(st, "ExtSubTable", st)
            if st.LookupType != 2:
                continue
            if st.Format == 1:
                for g, ps in zip(st.Coverage.glyphs, st.PairSet):
                    for r in ps.PairValueRecord:
                        out.setdefault((g, r.SecondGlyph), getattr(r.Value1, "XAdvance", 0) if r.Value1 else 0)
            else:
                c1, c2 = collections.defaultdict(list), collections.defaultdict(list)
                for g in st.Coverage.glyphs:
                    c1[st.ClassDef1.classDefs.get(g, 0)].append(g)
                for g in t.getGlyphOrder():
                    c2[st.ClassDef2.classDefs.get(g, 0)].append(g)
                for i, rec in enumerate(st.Class1Record):
                    for j, r2 in enumerate(rec.Class2Record):
                        v = getattr(r2.Value1, "XAdvance", 0) if r2.Value1 else 0
                        for a in c1.get(i, []):
                            for b in c2.get(j, []):
                                out.setdefault((a, b), v)
    return {p: v for p, v in out.items() if v}


def main():
    f = glyphsLib.GSFont(sys.argv[1])
    first, second = collections.defaultdict(set), collections.defaultdict(set)
    for g in f.glyphs:
        if g.rightKerningGroup:
            first[g.rightKerningGroup].add(g.name)
        if g.leftKerningGroup:
            second[g.leftKerningGroup].add(g.name)

    def side(tok, is_first):
        if tok.startswith("@"):
            return (first if is_first else second).get(re.sub(r"^@(MMK_[LR]_)?_?", "", tok), set())
        return {tok}

    def expand(pairs):
        out = {}
        for (a, b), v in sorted(pairs.items(), key=lambda kv: -(kv[0][0].startswith("@") + kv[0][1].startswith("@"))):
            for x in side(a, True):
                for y in side(b, False):
                    out[(x, y)] = v
        return out

    code = "\n".join(p.code for p in f.featurePrefixes) + "\n".join(x.code for x in f.features)
    start = code.find("feature kern {")
    kern = code[start:code.index("} kern;", start)] if start >= 0 else ""
    fea = expand({(m.group(1), m.group(2)): int(m.group(3)) for m in re.finditer(
        r"^\s*(?:enum\s+)?pos\s+(@?[\w.]+)\s+(@?[\w.]+)\s+(-?\d+);", kern, re.M)})
    kd = f.kerning.get(f.masters[0].id, {})
    kerning = expand({(a, b): v for a, d in kd.items() for b, v in d.items()})
    rel = release_pairs(sys.argv[2])
    print("release: %d kerned glyph pairs" % len(rel))
    for name, e in (("kern feature", fea), ("kerning", kerning)):
        print("%-12s %6d pairs; equal to the release %d; release pairs missing %d" % (
            name, len(e), sum(1 for p, v in e.items() if rel.get(p) == v), sum(1 for p in rel if p not in e)))
    print("kern feature pairs not equal in the kerning: %d" % sum(1 for p, v in fea.items() if kerning.get(p) != v))


if __name__ == "__main__":
    main()
