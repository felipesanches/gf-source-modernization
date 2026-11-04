#!/usr/bin/env python3
"""Question answered: which landed repositories (any route) might hide a kern-across-marks shaping
difference that the functional gate's kern+mark corpus never tried (gate gap G)?

Until 2026-11-03 the kern+mark corpus put only U+0301, U+0308 and U+0323 between a kerned pair.
Master kerning compiles to a kern lookup that ignores marks; a release kern lookup without
IgnoreMarks does not skip them. Per shipped style of every repository whose last landed.tsv row is
CLEAN*: whether a kern lookup lacks IgnoreMarks, the marks a shaper sees (GDEF class 3 glyphs'
codepoints, or without glyph classes the codepoints of general category M*, not default-ignorable),
and how many of them the old corpus tried. RISK: a kern lookup without IgnoreMarks and marks none of
which the old corpus tried. TESTED: such a lookup, and the old corpus tried at least one mark.

Usage: python3 -I tools/probes/ttf_gpos_kerning/kern_marks_risk.py > tools/probes/ttf_gpos_kerning/kern-marks-risk-<date>.tsv
"""
import csv, io, os, subprocess, unicodedata
from fontTools.ttLib import TTFont

W = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
GF = "/home/fsanches/compartilhado/google/fonts"
OLD = {0x0301, 0x0308, 0x0323}
IGNORABLE_MARKS = {0x034F, 0x17B4, 0x17B5, *range(0x180B, 0x180E), 0x180F, *range(0xFE00, 0xFE10),
                   *range(0xE0100, 0xE01F0)}


def release(commit, path):
    data = subprocess.run(["git", "-C", GF, "show", "%s:%s" % (commit, path)], capture_output=True).stdout
    return TTFont(io.BytesIO(data), lazy=True) if data else None


def main():
    last = {}
    for row in csv.reader(open(os.path.join(W, "landed.tsv")), delimiter="\t"):
        last[row[0]] = row[4]
    styles = {}
    for t in ("families.tsv", "families-next.tsv", "families-vfb.tsv", "families-binary.tsv"):
        for r in csv.DictReader(open(os.path.join(W, t)), delimiter="\t"):
            styles.setdefault(r["repo"], {})[r["style"]] = (r["commit"], r["shipped"])
    print("\t".join(["repo", "verdict", "style", "kern_flags", "glyph_classes", "marks", "old_corpus_marks", "risk"]))
    for repo in sorted(last):
        if not last[repo].startswith("CLEAN") or repo not in styles:
            continue
        for style, (commit, shipped) in sorted(styles[repo].items()):
            tt = release(commit, shipped)
            if tt is None or "GPOS" not in tt or not tt["GPOS"].table.FeatureList:
                continue
            g = tt["GPOS"].table
            idx = {i for fr in g.FeatureList.FeatureRecord if fr.FeatureTag == "kern" for i in fr.Feature.LookupListIndex}
            flags = sorted({g.LookupList.Lookup[i].LookupFlag for i in idx})
            if not flags:
                continue
            cmap = tt.getBestCmap()
            classes = "GDEF" in tt and tt["GDEF"].table.GlyphClassDef
            if classes:
                marks = {cp for cp, n in cmap.items() if classes.classDefs.get(n) == 3}
            else:
                marks = {cp for cp in cmap if unicodedata.category(chr(cp)).startswith("M") and cp not in IGNORABLE_MARKS}
            skips_marks = all(f & 0x0008 for f in flags)
            risk = "-" if skips_marks or not marks else ("TESTED" if marks & OLD else "RISK")
            print("\t".join([repo, last[repo], style, ",".join(map(str, flags)), "yes" if classes else "no",
                             str(len(marks)), str(len(marks & OLD)), risk]))


main()
