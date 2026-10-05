#!/usr/bin/env python3
"""Which releases carry FontForge's empty GPOS shell, empty GSUB shell, or a legacy kern only?

Question: across the pairing tables, which shipped binaries (FFTM present) have a GPOS
with 0 lookups while GSUB has lookups (the shell sharedLayoutScripts reproduces), the
reverse, or a `kern` table and no GPOS at all (the Smokum/Ultra case)? Independent of
next-emptygpos's census_layout_shells.py.

Signal read: presence of FFTM, kern; LookupList counts of GSUB/GPOS of column 9 (shipped).

Run (from /home/fsanches/compartilhado/gf-source-modernization):
  /home/fsanches/compartilhado/gftools/venv/bin/python3 investigations/next-emptygpos-verify/probes/shell_census.py families.tsv families-next.tsv
"""
import csv
import sys

from fontTools.ttLib import TTFont

seen, rows = set(), []
for fam in sys.argv[1:]:
    for r in csv.reader(open(fam), delimiter="\t"):
        if r[0] == "repo" or len(r) < 9:
            continue
        style, rel = r[6], r[8]
        if (style, rel) in seen:
            continue
        seen.add((style, rel))
        f = TTFont(rel)

        def n(tag):
            if tag not in f:
                return None
            t = f[tag].table
            return t.LookupList.LookupCount if t.LookupList else 0
        rows.append((style, "FFTM" in f, n("GSUB"), n("GPOS"), "kern" in f, fam))
emptygpos = [r for r in rows if r[1] and r[3] == 0 and (r[2] or 0) > 0]
emptygsub = [r for r in rows if r[1] and r[2] == 0 and (r[3] or 0) > 0]
kernonly = [r for r in rows if r[4] and r[3] is None]
print("styles", len(rows))
print("empty GPOS shell (FFTM, GPOS 0 lookups, GSUB>0):", len(emptygpos), [r[0] for r in emptygpos])
print("empty GSUB shell (FFTM, GSUB 0 lookups, GPOS>0):", len(emptygsub), [r[0] for r in emptygsub])
print("legacy kern, no GPOS:", len(kernonly), [(r[0], r[5]) for r in kernonly])
