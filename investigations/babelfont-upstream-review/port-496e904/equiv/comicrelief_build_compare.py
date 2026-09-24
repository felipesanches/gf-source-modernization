#!/usr/bin/env python3
"""Question answered: does the one intended .glyphs difference between babelfont 8b59bc3
and integration-ff-prs (ComicRelief-Regular: three component offsets -0 -> 0) change the
font gftools-builder3 e851b8b builds from it?

Converts the UNMODIFIED ComicRelief-Regular.sfd (recipe.source_text, recipe flags) with
both binaries, applies tools/workarounds.py as land.py does, builds each with
{buildVariable: false, removeOutlineOverlaps: false}, and compares every table with ttx
(head.modified and head.checkSumAdjustment ignored). Writes comicrelief/RESULT.txt.

Usage: TMPDIR=<existing dir> python3 comicrelief_build_compare.py <candidate-babelfont>
"""
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, "/home/fsanches/compartilhado/sfd-reland/tools")
sys.path.insert(0, HERE)
import recipe  # noqa: E402
import workarounds  # noqa: E402
import land  # noqa: E402
import gate_candidate  # noqa: E402

W = os.path.join(HERE, "comicrelief")
shutil.rmtree(W, ignore_errors=True)
os.makedirs(W)
row = [r for r in recipe.rows() if r["style"] == "ComicRelief-Regular"][0]
src = os.path.join(W, "ComicRelief-Regular.sfd")
open(src, "w", encoding="utf-8", errors="replace").write(recipe.source_text(row))
flags = recipe.flags_for(open(src, encoding="utf-8", errors="replace").read(), row["shipped"])
for who, b in (("ref", land.BF), ("cand", sys.argv[1])):
    t = os.path.join(W, who, "sources")
    os.makedirs(t)
    g = os.path.join(t, "ComicRelief-Regular.glyphs")
    subprocess.run([b, src, g] + flags, check=True, capture_output=True)
    workarounds.apply_all(g, src)
    open(os.path.join(t, "config.yaml"), "w").write(
        "buildVariable: false\nremoveOutlineOverlaps: false\nsources:\n  - ComicRelief-Regular.glyphs\n")
    subprocess.run([land.B3, "sources/config.yaml"], cwd=os.path.join(W, who), check=True,
                   capture_output=True)
ttf = "fonts/ttf/ComicRelief-Regular.ttf"
r = gate_candidate.table_diff(os.path.join(W, "ref", ttf), os.path.join(W, "cand", ttf), W)
out = "\n".join(r) or ("ComicRelief-Regular ref vs cand TTF: every table identical once "
                       "head.modified/checkSumAdjustment are ignored")
open(os.path.join(W, "RESULT.txt"), "w").write(out + "\n")
print(out)
