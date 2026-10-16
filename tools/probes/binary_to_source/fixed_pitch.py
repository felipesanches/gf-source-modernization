#!/usr/bin/env python3
"""Question answered: does any shipped font of families-binary.tsv declare itself fixed pitch
(post.isFixedPitch nonzero, or OS/2 PANOSE bProportion 9, monospaced)? If none does, the
babelfont branches that read or infer isFixedPitch change no binary family.

  GF=<google/fonts clone> ARCHIVE=<repo archive> python3 fixed_pitch.py

Fonts are read with `git show` from the google/fonts clone at each row's commit, or for a row
whose base is another repository from its bare mirror in the repo archive. Prints each
fixed-pitch font and a total.
"""
import csv
import io
import os
import subprocess
import sys

from fontTools.ttLib import TTFont

HERE = os.path.dirname(os.path.abspath(__file__))
TSV = os.path.join(HERE, "..", "..", "..", "families-binary.tsv")
GF = os.environ.get("GF", "")            # a google/fonts clone
ARCHIVE = os.environ.get("ARCHIVE", "")  # the repo archive of bare mirrors

if not GF or not ARCHIVE:
    sys.exit(__doc__)
rows = list(csv.DictReader(open(TSV), delimiter="\t"))
fixed = 0
for r in rows:
    if r["base"] == "google/fonts":
        repo, path = GF, r["shipped"]
    else:
        repo, path = os.path.join(ARCHIVE, r["base"] + ".git"), r["source"]
    data = subprocess.run(["git", "-C", repo, "show", "%s:%s" % (r["commit"], path)],
                          capture_output=True, check=True).stdout
    font = TTFont(io.BytesIO(data), lazy=True)
    post, proportion = font["post"].isFixedPitch, font["OS/2"].panose.bProportion
    if post or proportion == 9:
        fixed += 1
        print("%s %s: post.isFixedPitch %d, PANOSE bProportion %d" % (r["repo"], r["style"], post, proportion))
print("total: %d fonts, %d fixed pitch" % (len(rows), fixed))
