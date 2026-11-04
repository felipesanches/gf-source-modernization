#!/usr/bin/env python3
"""Question answered: which flag-0 kern lookups on the binary route read wrongly into master
kerning, because a shaper skips marks the release's lookup does not skip?

Master kerning compiles to a kern lookup that ignores marks. A release kern lookup with flag 0 is
the same only when no glyph is a mark. With a GDEF glyph class definition the marks are its class
3. Without one, a shaper classes glyphs by codepoint: a mark (Mn, Mc, Me) that is not
default-ignorable (HarfBuzz synthesize_glyph_classes). Forum (no GDEF, U+0300..U+030C encoded)
was the case that showed it: 7195 of 8300 kern+mark runs differed in the acceptance run.

Per style whose kern lookups all have flag 0 (census-<date>.tsv): whether GDEF has glyph classes,
how many glyphs a shaper takes for marks, and the verdict SAFE (no marks) or MARKS.

Usage: python3 -I tools/probes/ttf_gpos_kerning/marks.py tools/probes/ttf_gpos_kerning/census-<date>.tsv > tools/probes/ttf_gpos_kerning/marks-<date>.tsv
"""
import csv, os, sys, unicodedata
from fontTools.ttLib import TTFont

W = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
GF = "/home/fsanches/compartilhado/google/fonts/"
# Default_Ignorable_Code_Point characters with a mark general category (Unicode 16 DerivedCoreProperties)
IGNORABLE_MARKS = {0x034F, 0x17B4, 0x17B5, *range(0x180B, 0x180E), 0x180F, *range(0xFE00, 0xFE10),
                   *range(0xE0100, 0xE01F0)}


def unicode_mark(cp):
    return unicodedata.category(chr(cp)).startswith("M") and cp not in IGNORABLE_MARKS


def main():
    shipped = {(r["repo"], r["style"]): r["shipped"]
               for r in csv.DictReader(open(os.path.join(W, "families-binary.tsv")), delimiter="\t")}
    print("\t".join(["repo", "style", "gdef_classes", "marks", "examples", "verdict"]))
    for r in csv.DictReader(open(sys.argv[1]), delimiter="\t"):
        if r["flags"] != "0":
            continue
        tt = TTFont(GF + shipped[(r["repo"], r["style"])], lazy=True)
        classes = "GDEF" in tt and tt["GDEF"].table.GlyphClassDef
        if classes:
            marks = sorted(g for g, c in classes.classDefs.items() if c == 3)
        else:
            marks = sorted({g for cp, g in tt.getBestCmap().items() if unicode_mark(cp)})
        print("\t".join([r["repo"], r["style"], "yes" if classes else "no", str(len(marks)),
                         ",".join(marks[:4]), "MARKS" if marks else "SAFE"]))


main()
