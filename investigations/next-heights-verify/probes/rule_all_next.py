#!/usr/bin/env python3
"""Question answered: across EVERY style of families-next.tsv (not just the unit), does
FontForge's rule -- FFTM-selected vintage, SFFindGID lookup (primary or AltUni), the
.sfd's own private BlueValues if any -- reproduce the released sxHeight/sCapHeight?
Any style whose rule value differs is a height row somebody must own; styles whose
harness build never finished (BUILD-FAILED) are included, since their gate cannot show
height rows yet. Uses ../../heights/ff_heights_probe.py.

Run: /home/fsanches/compartilhado/gftools/venv/bin/python3 rule_all_next.py > ../runs/rule_all_next.txt
"""
import subprocess
import sys

from fontTools.ttLib import TTFont

sys.path.insert(0, "/home/fsanches/compartilhado/gf-source-modernization/investigations/heights")
import ff_heights_probe as P  # noqa: E402

ARC = "/home/fsanches/compartilhado/upstream_repos/repo_archive"
FAM = "/home/fsanches/compartilhado/gf-source-modernization/families-next.tsv"
E, FIX = 2082844800, 1337023489
with open(FAM) as fh:
    head = fh.readline().rstrip("\n").split("\t")
    rows = [dict(zip(head, l.rstrip("\n").split("\t"))) for l in fh]
for r in rows:
    p = f"{r['lic']}/{r['family']}/{r['source']}" if r["kind"] == "hg" else r["source"]
    q = subprocess.run(["git", "-C", f"{ARC}/{r['base']}.git", "show", f"{r['commit']}:{p}"], capture_output=True)
    if q.returncode:
        print(f"{r['style']}\tNO SOURCE"); continue
    font = P.parse(q.stdout.decode("utf-8", "replace"))
    rel = TTFont(r["shipped"])
    o = rel["OS/2"]
    if o.version < 2:
        print(f"{r['style']}\trelease OS/2 v{o.version}: no heights"); continue
    year = 2011 if "FFTM" in rel and rel["FFTM"].FFTimeStamp - E < FIX else 2012
    out = []
    for lab, lst, want in (("x", P.XH, o.sxHeight), ("cap", P.CAP, o.sCapHeight)):
        v = P.exported(P.standard_height(P.V(year), font, lst)[0])
        out.append(f"{lab} rule {v} release {want} {'ok' if v == want else 'DIFF'}")
    print(f"{r['style']}\tFFTM-rule {year}\tsfd-blues {font['blues']}\t" + "\t".join(out))
