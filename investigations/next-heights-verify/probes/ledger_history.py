#!/usr/bin/env python3
"""Question answered: which google/fonts commits changed Ledger-Regular.ttf after the
2012 googlefontdirectory-hg binary, and which table VALUES did each change? In
particular: is the U+00A0 advance 0 -> 281 a google/fonts edit (0436d99c0), did any
edit touch OS/2 (so the 487 x-height predates 2020), and is the hg 52f780bc binary
identical to google/fonts' initial import 90abd17b4?

Compares, table by table (fontTools decompiled data, not only raw bytes), the
hg binary -> 90abd17b4 -> 0436d99c0 -> f8265bddf, and prints hmtx of U+00A0 / space,
OS/2 sxHeight/sCapHeight/usWeightClass, head.fontRevision and name ID 5.

Run: /home/fsanches/compartilhado/gftools/venv/bin/python3 ledger_history.py > ../runs/ledger_history.txt
"""
import hashlib
import io
import subprocess

from fontTools.ttLib import TTFont

GF = "/home/fsanches/compartilhado/google/fonts"
HG = "/home/fsanches/compartilhado/upstream_repos/repo_archive/googlefonts/googlefontdirectory-hg.git"
HGC = "52f780bc9d197280a9f430574e179a5f233c56b6"


def blob(repo, rev, path):
    return subprocess.run(["git", "-C", repo, "show", f"{rev}:{path}"], capture_output=True,
                          check=True).stdout


states = [("hg 52f780bc", blob(HG, HGC, "ofl/ledger/Ledger-Regular.ttf"))]
for rev in ("90abd17b4", "0436d99c0", "f8265bddf"):
    states.append((f"gf {rev}", blob(GF, rev, "ofl/ledger/Ledger-Regular.ttf")))
with open(f"{GF}/ofl/ledger/Ledger-Regular.ttf", "rb") as fh:
    states.append(("gf working tree (release b5efa9c32e8f)", fh.read()))

prev = None
for label, data in states:
    f = TTFont(io.BytesIO(data))
    cm = f.getBestCmap()
    o = f["OS/2"]
    name5 = f["name"].getDebugName(5)
    print(f"{label}: sha256 {hashlib.sha256(data).hexdigest()[:16]}  nbsp adv "
          f"{f['hmtx'][cm[0xA0]][0]} ({cm[0xA0]})  space adv {f['hmtx'][cm[0x20]][0]}  "
          f"OS/2 v{o.version} x={o.sxHeight} cap={o.sCapHeight} wc={o.usWeightClass}  "
          f"fontRevision {f['head'].fontRevision:.4f}  name5 {name5!r}")
    if prev is not None:
        changed = []
        for tag in sorted(set(prev.keys()) | set(f.keys())):
            if tag == "GlyphOrder":
                continue
            a = prev.reader[tag] if tag in prev.reader.tables else None
            b = f.reader[tag] if tag in f.reader.tables else None
            if a != b:
                changed.append(tag)
        print(f"    raw tables changed vs previous: {changed}")
    prev = f
