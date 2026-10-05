#!/usr/bin/env python3
"""d3_cmap_summary.py -- beyond the table rows: rendering and cmap, per verification build.

Question answered: for every scratch build <Style>-fstype-verify-<run>, did diffenator3
(the d3.json baseline.sh wrote, run with --succinct) report ANY glyph or word
difference at the default location (with --succinct an absent key means none), what
did its kern comparison say, and which codepoints does the build gain or lose against
the shipped font (land.py requires none)?

Run: $PY d3_cmap_summary.py <run> ...
"""
import csv
import glob
import json
import sys

from fontTools.ttLib import TTFont

V = "/home/fsanches/compartilhado/gf-source-modernization/investigations/next-fstype-verify/runs"
S = "/home/fsanches/compartilhado/sfd-reland-scratch/fstype-verify/baseline"
rows = {r["style"]: r for r in csv.DictReader(open(V + "/families-verify.tsv"), delimiter="\t")}
for run in sys.argv[1:]:
    for st in sorted(rows):
        d = "%s/%s-fstype-verify-%s" % (S, st, run)
        built = glob.glob(d + "/fonts/ttf/*.ttf")
        if len(built) != 1:
            continue
        j = json.load(open(d + "/d3.json"))
        loc_keys = sorted({k for l in j.get("locations", []) for k in l if k != "location"})
        a = set(TTFont(rows[st]["shipped"]).getBestCmap())
        b = set(TTFont(built[0]).getBestCmap())
        print("%s\t%s\td3_location_diff_keys=%s\tkerns=%s\tcmap_gained=%s\tcmap_lost=%s" % (
            run, st, loc_keys or "none", json.dumps(j.get("kerns"))[:60],
            sorted(b - a), sorted(a - b)))
