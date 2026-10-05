#!/usr/bin/env python3
"""names_beyond_gate.py -- what the table gate does not compare, per verification run.

Question answered: for each style built in runs/<run>/ (scratch build dir
$S/baseline/<Style>-fstype-verify-<run>/fonts/ttf/*.ttf), do the Windows-English name
records 1,2,3,4,5,6,16,17 and OS/2 fsType / usWeightClass / fsSelection, head.macStyle
/ fontRevision match the shipped font (families-verify.tsv's `shipped` column)?
The gate ACCEPTS name, fs_selection, mac_style and font_revision, so a CLEAN verdict
says nothing about them.

Run: $PY names_beyond_gate.py <run> [Style ...]  (run = v2-fstype, v3a-elweight, ...)
"""
import csv
import glob
import sys

from fontTools.ttLib import TTFont

V = "/home/fsanches/compartilhado/gf-source-modernization/investigations/next-fstype-verify/runs"
S = "/home/fsanches/compartilhado/sfd-reland-scratch/fstype-verify/baseline"
rows = {r["style"]: r for r in csv.DictReader(open(V + "/families-verify.tsv"), delimiter="\t")}
run = sys.argv[1]
styles = sys.argv[2:] or sorted(rows)
for st in styles:
    built = glob.glob("%s/%s-fstype-verify-%s/fonts/ttf/*.ttf" % (S, st, run))
    if len(built) != 1:
        continue
    a, b = TTFont(rows[st]["shipped"]), TTFont(built[0])
    out = []
    for label, fa, fb in (
            ("fsType", a["OS/2"].fsType, b["OS/2"].fsType),
            ("usWeightClass", a["OS/2"].usWeightClass, b["OS/2"].usWeightClass),
            ("fsSelection", a["OS/2"].fsSelection, b["OS/2"].fsSelection),
            ("macStyle", a["head"].macStyle, b["head"].macStyle),
            ("fontRevision", round(a["head"].fontRevision, 4), round(b["head"].fontRevision, 4))):
        out.append("%s %-14s %r / %r" % ("==" if fa == fb else "!=", label, fa, fb))
    for nid in (1, 2, 3, 4, 5, 6, 16, 17, 18):
        x = a["name"].getName(nid, 3, 1, 0x409)
        y = b["name"].getName(nid, 3, 1, 0x409)
        x = x.toUnicode() if x else None
        y = y.toUnicode() if y else None
        out.append("%s name %-9d %r / %r" % ("==" if x == y else "!=", nid, x, y))
    print("== %s  (%s): shipped / built=%s" % (st, run, built[0].split("/")[-1]))
    for o in out:
        print("   " + o)
