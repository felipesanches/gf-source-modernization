#!/usr/bin/env python3
"""Question answered: for every style in families.tsv + families-next.tsv, does the
release's glyph 0 equal FontForge's synthesized .notdef (dumpmissingglyph, tottf.c)
exactly when the paired .sfd has no glyph named .notdef? Also: is the release
post.isFixedPitch equal to FontForge's one-width rule on the release advances?
Run from gf-source-modernization: $PY notdef_census.py"""
import os, re, sys
sys.path.insert(0, "/home/fsanches/compartilhado/gf-source-modernization/tools")
os.chdir("/home/fsanches/compartilhado/gf-source-modernization")
import recipe
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
W = "/home/fsanches/compartilhado/gf-source-modernization"
for t in ("families.tsv", "families-next.tsv"):
    os.environ["FAMILIES"] = os.path.join(W, t)
    for row in recipe.rows():
        if not row.get("repo") or not os.path.exists(row["shipped"]):
            continue
        try:
            sfd = recipe.source_text(row)
        except Exception as e:
            print(row["style"], "NOSRC", e); continue
        has = re.search(r"^StartChar: \.notdef\s*$", sfd, re.M) is not None
        asc = int(re.search(r"^Ascent: (\d+)", sfd, re.M).group(1))
        desc = int(re.search(r"^Descent: (\d+)", sfd, re.M).group(1))
        em = asc + desc; stem = em // 30; ymax = min(2 * em // 3, asc); xmax = 6 * stem + em // 10
        f = TTFont(row["shipped"]); g0 = f.getGlyphOrder()[0]
        scale = f["head"].unitsPerEm / em
        p = RecordingPen(); f.getGlyphSet()[g0].draw(p)
        pts = [tuple(a[0]) for op, a in p.value if op in ("moveTo", "lineTo")]
        want = [(stem, 0), (stem, ymax), (xmax, ymax), (xmax, 0), (2*stem, stem), (xmax-stem, stem), (xmax-stem, ymax-stem), (2*stem, ymax-stem)]
        want = [(round(x*scale), round(y*scale)) for x, y in want]
        synth = sorted(pts) == sorted(want)
        adv = f["hmtx"][g0][0]
        print("\t".join([row["style"], "src_notdef=%d" % has, "release_synth=%d" % synth,
                         "adv=%d" % adv, "fftm=%s" % ("FFTM" in f), "fixed=%d" % f["post"].isFixedPitch]))
