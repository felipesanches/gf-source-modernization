#!/usr/bin/env python3
"""Which releases carry FontForge's shared-script layout shell, and which kern only
through a legacy `kern` table?

Question: FontForge's OpenType exporter gives GSUB and GPOS the same script list
(SFScriptsInLookups in lookups.c ignores its `gpos` argument; SFLangsInScript gives a
script with no lookups in a table one dummy default LangSys). So a FontForge release
whose source has lookups in only one table carries an EMPTY shell of the other. With
OpenType output off (neither 'opentype' nor 'apple' generate flag), FontForge writes no
GSUB/GPOS/GDEF at all and kerning goes to a legacy `kern` table. For every style in
the pairing tables, which of these cases is the release?

Signal read, per release (the `shipped` column of the pairing table):
  FFTM         present -> exported by FontForge (FFTimeStamp decoded to a date)
  GSUB/GPOS    present? script tags, feature count, lookup count
  kern         legacy table present? number of pairs in subtable 0
  class        empty-GPOS-shell | empty-GSUB-shell | both-with-lookups |
               kern-only | no-layout | other
  symmetric    for FontForge releases with both tables: are the script tag sets equal?
               (FontForge always makes them equal; a 'no' would contradict the rule)

Run:
    /home/fsanches/compartilhado/gftools/venv/bin/python3 census_layout_shells.py \
        /home/fsanches/compartilhado/gf-source-modernization/families.tsv \
        /home/fsanches/compartilhado/gf-source-modernization/families-next.tsv
Output: one TSV row per style on stdout, then a summary.
"""
import csv
import datetime
import sys

from fontTools.ttLib import TTFont

MAC_EPOCH = datetime.datetime(1904, 1, 1)


def layout(font, tag):
    if tag not in font:
        return None
    t = font[tag].table
    scripts = sorted(r.ScriptTag for r in t.ScriptList.ScriptRecord) if t.ScriptList else []
    nf = len(t.FeatureList.FeatureRecord) if t.FeatureList else 0
    nl = len(t.LookupList.Lookup) if t.LookupList else 0
    return scripts, nf, nl


def classify(gsub, gpos, kern):
    def empty(x):
        return x is not None and x[1] == 0 and x[2] == 0

    def full(x):
        return x is not None and (x[1] or x[2])
    if gsub is None and gpos is None:
        return "kern-only" if kern else "no-layout"
    if full(gsub) and empty(gpos):
        return "empty-GPOS-shell"
    if full(gpos) and empty(gsub):
        return "empty-GSUB-shell"
    if full(gsub) and full(gpos):
        return "both-with-lookups"
    if full(gsub) and gpos is None:
        return "GSUB-only"
    if full(gpos) and gsub is None:
        return "GPOS-only"
    return "other"


def main(paths):
    seen = set()
    counts = {}
    print("\t".join(["table", "style", "fftm_date", "class", "gsub_scripts", "gpos_scripts",
                     "symmetric", "kern_pairs", "shipped"]))
    for p in paths:
        for row in csv.DictReader(open(p), delimiter="\t"):
            key = (row["style"], row["shipped"])
            if key in seen:
                continue
            seen.add(key)
            f = TTFont(row["shipped"], lazy=True)
            date = "-"
            if "FFTM" in f:
                date = (MAC_EPOCH + datetime.timedelta(
                    seconds=f["FFTM"].FFTimeStamp)).strftime("%Y-%m-%d")
            gsub, gpos = layout(f, "GSUB"), layout(f, "GPOS")
            kern = 0
            if "kern" in f:
                kern = sum(len(st.kernTable) for st in f["kern"].kernTables
                           if hasattr(st, "kernTable"))
            cls = classify(gsub, gpos, kern)
            sym = "-"
            if gsub is not None and gpos is not None:
                sym = "yes" if gsub[0] == gpos[0] else "no"
            counts.setdefault((cls, date != "-"), []).append(row["style"])
            print("\t".join([p.rsplit("/", 1)[-1], row["style"], date, cls,
                             ",".join(gsub[0]) if gsub else "-",
                             ",".join(gpos[0]) if gpos else "-", sym, str(kern),
                             row["shipped"]]))
    print()
    for (cls, ff), styles in sorted(counts.items()):
        print("# %-18s FontForge=%-5s %3d  %s" % (cls, ff, len(styles),
                                                ", ".join(sorted(styles)) if len(styles) < 40 else ""))


if __name__ == "__main__":
    main(sys.argv[1:])
