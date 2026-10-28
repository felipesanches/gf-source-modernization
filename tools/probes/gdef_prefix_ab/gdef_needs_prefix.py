#!/usr/bin/env python3
"""For every binary-only family's release font: would the classes a compiler derives from the
converted source (Mark = GDEF class 3 via the reader's categories; Base/Ligature = glyphs that
carry attaching anchors, i.e. MarkBasePos/MarkLigPos bases) differ from the release's GDEF
classes, and would that matter (a lookup filters on glyph class, or the release's GDEF has no
marks so the build writes none)?  Columns: repo style classes(1/2/3/4) derived-diff reads marks NEED
Usage: gdef_needs_prefix.py [repo ...]   (run from gf-source-modernization)
"""
import csv, os, subprocess, sys, tempfile
sys.path.insert(0, "tools")
from table_gate import _reads_glyph_class
from fontTools.ttLib import TTFont

GF = "/home/fsanches/compartilhado/gfonts"
only = set(sys.argv[1:])
rows = [r for r in csv.DictReader(open("families-binary.tsv"), delimiter="\t") if not only or r["repo"] in only]
tmp = tempfile.mkdtemp(prefix="gdef-need-", dir=os.environ.get("TMPDIR", "/home/fsanches/compartilhado/tmp"))

def anchored(gpos):
    bases, ligs = set(), set()
    if not gpos or not gpos.table.LookupList:
        return bases, ligs
    for lk in gpos.table.LookupList.Lookup:
        for st in lk.SubTable:
            if st.LookupType == 9:
                st = st.ExtSubTable
            if st.LookupType == 4:
                bases.update(st.BaseCoverage.glyphs)
            elif st.LookupType == 5:
                ligs.update(st.LigatureCoverage.glyphs)
    return bases, ligs

for r in rows:
    p = os.path.join(tmp, os.path.basename(r["shipped"]))
    with open(p, "wb") as fh:
        fh.write(subprocess.run(["git", "-C", GF, "show", "%s:%s" % (r["commit"], r["shipped"])], capture_output=True, check=True).stdout)
    tt = TTFont(p)
    gdef = tt["GDEF"].table if "GDEF" in tt else None
    cd = gdef.GlyphClassDef.classDefs if gdef and gdef.GlyphClassDef else None
    if cd is None:
        print("%-22s %-28s no-GlyphClassDef" % (r["repo"], r["style"]))
        continue
    rel = {g: c for g, c in cd.items() if c}
    bases, ligs = anchored(tt.get("GPOS"))
    derived = {g: 3 for g, c in rel.items() if c == 3}
    for g in bases:
        derived.setdefault(g, 1)
    for g in ligs:
        derived.setdefault(g, 2)
    diff = {g for g in set(rel) | set(derived) if rel.get(g) != derived.get(g)}
    counts = "/".join(str(sum(1 for c in rel.values() if c == k)) for k in (1, 2, 3, 4))
    reads = _reads_glyph_class(p)
    marks = any(c == 3 for c in rel.values())
    need = bool(diff) and (reads or not marks)
    print("%-22s %-28s classes=%-18s diff=%-5d reads=%-5s marks=%-5s %s" % (r["repo"], r["style"], counts, len(diff), reads, marks, "NEED" if need else "-"))
