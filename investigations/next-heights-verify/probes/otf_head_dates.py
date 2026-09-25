#!/usr/bin/env python3
"""Question answered: does the sibling src/<X>.otf in the base tree carry the SAME
head.created / head.modified as the release's FFTM sourceCreated / sourceModified?

FontForge copies an opened OpenType font's head.created/modified into
sf->creationtime/modtime and writes them back as FFTM's source dates when it
generates. Equal dates tie the release to a font FontForge opened with those head
dates -- i.e. to this .otf (or a byte-level twin of its head) -- which is the
provenance claim behind the BlueValues edits. Pairing: families-next.tsv.

Run: /home/fsanches/compartilhado/gftools/venv/bin/python3 otf_head_dates.py > ../runs/otf_head_dates.txt
"""
import io
import subprocess
import time

from fontTools.ttLib import TTFont

ARC = "/home/fsanches/compartilhado/upstream_repos/repo_archive/googlefonts/googlefontdirectory-hg.git"
FAM = "/home/fsanches/compartilhado/sfd-reland/families-next.tsv"
E = 2082844800
STYLES = """KottaOne-Regular Ledger-Regular LilitaOne-Regular Lustria-Regular Macondo-Regular
Magra-Bold MergeOne-Regular OleoScript-Bold OleoScript-Regular OleoScriptSwashCaps-Bold
OleoScriptSwashCaps-Regular Rambla-Bold Rambla-BoldItalic Rosarivo-Italic Sail-Regular
TextMeOne-Regular Magra-Regular Rambla-Italic Rambla-Regular Rosarivo-Regular""".split()


def u(t):
    return time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(t - E))


with open(FAM) as fh:
    head = fh.readline().rstrip("\n").split("\t")
    rows = {r["style"]: r for r in (dict(zip(head, l.rstrip("\n").split("\t"))) for l in fh)}
for s in STYLES:
    r = rows[s]
    rel = TTFont(r["shipped"])
    f = rel["FFTM"]
    p = f"{r['lic']}/{r['family']}/" + r["source"].replace("-TTF.sfd", ".otf")
    otf = TTFont(io.BytesIO(subprocess.run(["git", "-C", ARC, "show", f"{r['commit']}:{p}"],
                                           capture_output=True, check=True).stdout))
    h = otf["head"]
    same = (h.created == f.sourceCreated, h.modified == f.sourceModified)
    print(f"{s:30s} FFTM src {u(f.sourceCreated)} / {u(f.sourceModified)}   "
          f"otf head {u(h.created)} / {u(h.modified)}   equal={same}   release head "
          f"{u(rel['head'].created)} / {u(rel['head'].modified)}")
