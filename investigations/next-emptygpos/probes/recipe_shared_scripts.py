#!/usr/bin/env python3
"""Proposed recipe rule: which styles get builder3's `sharedLayoutScripts: true`?

Question: the option reproduces FontForge's shared GSUB/GPOS script list. Which
releases need it, asked of the release as recipe.py asks every other fidelity question?

Rule (narrowed by runs/13 and runs/15, where turning it on for every FontForge
OpenType-mode release opened GSUB.script_list rows): the release was exported by
FontForge (it has an FFTM table) AND carries a GPOS with no lookups AND a GSUB with
lookups -- FontForge's empty GPOS shell. That empty table is the one that changes
shaping (HarfBuzz skips fallback mark positioning when a GPOS exists); an empty GSUB
shell is inert and the gate already accepts it.

Signal read: FFTM presence; GPOS/GSUB LookupList counts of the `shipped` release.

Run:
    /home/fsanches/compartilhado/gftools/venv/bin/python3 recipe_shared_scripts.py \
        <pairing.tsv> [<pairing.tsv> ...]
Prints: style <TAB> yes|no <TAB> reason
"""
import csv
import sys

from fontTools.ttLib import TTFont


def shared_layout_scripts(shipped):
    f = TTFont(shipped, lazy=True)
    if "FFTM" not in f:
        return False, "not exported by FontForge (no FFTM)"
    if "GPOS" not in f or "GSUB" not in f:
        return False, "no GPOS/GSUB pair"
    gpos = f["GPOS"].table.LookupList
    gsub = f["GSUB"].table.LookupList
    ngpos = len(gpos.Lookup) if gpos else 0
    ngsub = len(gsub.Lookup) if gsub else 0
    if ngpos == 0 and ngsub > 0:
        return True, "FontForge empty GPOS shell (0 lookups; GSUB has %d)" % ngsub
    return False, "GPOS has %d lookups, GSUB %d" % (ngpos, ngsub)


def main():
    seen = set()
    for p in sys.argv[1:]:
        for row in csv.DictReader(open(p), delimiter="\t"):
            if row["style"] in seen:
                continue
            seen.add(row["style"])
            yes, why = shared_layout_scripts(row["shipped"])
            print("%s\t%s\t%s" % (row["style"], "yes" if yes else "no", why))


if __name__ == "__main__":
    main()
