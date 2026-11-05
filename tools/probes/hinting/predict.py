#!/usr/bin/env python3
"""What will functional_gate's hinting check say about each repository, before building it?

Usage: predict.py census.tsv [published.txt] > prediction.tsv
Our builds (gftools-rust 1e638bd, single-master statics) all carry the same hinting: prep
= the smart_dropout setup, gasp 65535:15, no fpgm, no glyph programs (checked on 24 built
fonts, 2026-11-05). So a font passes only if its release is not instructed and has exactly
that prep or none: the gate accepts what fontspector asks for (gasp 65535:15 in place of any
other, the smart_dropout prep where the release has none; Felipe, 2026-11-05).
The census does not see whether a prep CALLs the font program; a prep other than the
smart_dropout setup without glyph programs is reported as probably instructed (all 5 such
releases were).
Prints repo, font, prediction (PASS, or FAIL with the reasons) and, with published.txt (one
repo per line), whether the repo is published.
"""
import csv, sys

published = set(open(sys.argv[2]).read().split()) if len(sys.argv) > 2 else None
print("repo\tfont\tprediction\treasons" + ("\tpublished" if published is not None else ""))
for r in csv.DictReader(open(sys.argv[1]), delimiter="\t"):
    why = []
    if r["class"] in ("other", "ttfautohint"):
        why.append("release instructed (%s glyph programs, %s)" % (r["glyphs_with_instructions"], r["class"]))
    if r["smart_dropout"] != "exact" and r["prep"] != "-" and not why:
        # the census does not disassemble; the 5 such releases (2026-11-05) all CALL the fpgm
        why.append("release instructed (prep %s bytes, not the smart_dropout setup; calls the font program?)" % r["prep"])
    row = [r["repo"], r["font"], "FAIL" if why else "PASS", "; ".join(why)]
    if published is not None:
        row.append("yes" if r["repo"] in published else "no")
    print("\t".join(row))
