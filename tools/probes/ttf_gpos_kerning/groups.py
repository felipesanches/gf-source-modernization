#!/usr/bin/env python3
"""Question answered: for the SIMPLE styles of census.py, can the format 2 class pairs become kerning
groups as the model (and Glyphs) has them -- every glyph in at most one first-side and one second-side
group across all the `kern` lookups' class definitions (class 0 aside)?

Usage: python3 -I tools/probes/ttf_gpos_kerning/groups.py > tools/probes/ttf_gpos_kerning/groups-<date>.tsv
"""
import csv, os, sys
from fontTools.ttLib import TTFont

HERE = os.path.dirname(os.path.abspath(__file__))
GF = "/home/fsanches/compartilhado/google/fonts/"
W = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))


def main():
    simple = {(r["repo"], r["style"]) for r in csv.DictReader(open(os.path.join(HERE, "census-2026-11-03.tsv")), delimiter="\t") if r["verdict"] == "SIMPLE"}
    shipped = {(r["repo"], r["style"]): r["shipped"] for r in csv.DictReader(open(os.path.join(W, "families-binary.tsv")), delimiter="\t")}
    print("repo\tstyle\tformat2_subtables\tfirst_side_conflicts\tsecond_side_conflicts\tverdict")
    for key in sorted(simple):
        g = TTFont(GF + shipped[key], lazy=True)["GPOS"].table
        idx = sorted({i for fr in g.FeatureList.FeatureRecord if fr.FeatureTag == "kern" for i in fr.Feature.LookupListIndex})
        first, second, n = {}, {}, 0
        c1 = c2 = 0
        for i in idx:
            lk = g.LookupList.Lookup[i]
            for st in lk.SubTable:
                st = st.ExtSubTable if lk.LookupType == 9 else st
                if st.Format != 2:
                    continue
                n += 1
                covered = set(st.Coverage.glyphs)
                members1 = {}
                for gl in covered:
                    members1.setdefault(st.ClassDef1.classDefs.get(gl, 0), set()).add(gl)
                for cls, glyphs in members1.items():
                    gs = frozenset(glyphs)
                    for gl in glyphs:
                        if first.setdefault(gl, gs) != gs:
                            c1 += 1
                members2 = {}
                for gl, cls in st.ClassDef2.classDefs.items():
                    if cls:
                        members2.setdefault(cls, set()).add(gl)
                for cls, glyphs in members2.items():
                    gs = frozenset(glyphs)
                    for gl in glyphs:
                        if second.setdefault(gl, gs) != gs:
                            c2 += 1
        print("\t".join([key[0], key[1], str(n), str(c1), str(c2), "GROUPS" if not (c1 or c2) else "CONFLICT"]))


if __name__ == "__main__":
    sys.exit(main())
