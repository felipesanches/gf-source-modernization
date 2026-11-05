#!/usr/bin/env python3
"""Which kind of hinting does each shipped font carry?

Usage: census.py <families.tsv>... > census.tsv
Reads the `repo` and `shipped` columns of each table and prints, per shipped font
(a relative `shipped` path is read from the google/fonts clone in $GF, default
/home/fsanches/compartilhado/google/fonts):
  repo  font  class  glyphs_with_instructions  glyphs  smart_dropout  prep  fpgm  gasp  name5
smart_dropout: prep contains the sequence the smart_dropout check (fontspector) expects,
  B8 01 FF 85 B0 04 8D (PUSHW 511 SCANCTRL PUSHB 4 SCANTYPE); "exact" when that is all of prep
prep, fpgm: program lengths in bytes (- when absent); gasp: its ranges as ppem:behaviour
class is
  none          no fpgm, prep or glyph programs
  ttfautohint   name ID 5 records ttfautohint (its version and options)
  no-glyph-code fpgm/prep only, no glyph carries instructions
  other         glyph programs from another hinter (FontLab, VTT, FontForge, by hand)
"""
import csv, os, sys
from fontTools.ttLib import TTFont

SMART = bytes([0xB8, 0x01, 0xFF, 0x85, 0xB0, 0x04, 0x8D])

def classify(path):
    f = TTFont(path, lazy=True)
    name5 = ""
    if "name" in f:
        r = f["name"].getName(5, 3, 1, 0x409) or f["name"].getName(5, 1, 0, 0)
        name5 = str(r) if r else ""
    n = withcode = 0
    if "glyf" in f:
        g = f["glyf"]
        for gn in f.getGlyphOrder():
            n += 1
            gl = g[gn]
            if hasattr(gl, "program") and gl.program and len(gl.program.getBytecode()):
                withcode += 1
    tables = any(t in f for t in ("fpgm", "prep"))
    if "ttfautohint" in name5:
        cls = "ttfautohint"
    elif withcode:
        cls = "other"
    elif tables:
        cls = "no-glyph-code"
    else:
        cls = "none"
    prep = f["prep"].program.getBytecode() if "prep" in f and hasattr(f["prep"], "program") else None
    fpgm = f["fpgm"].program.getBytecode() if "fpgm" in f and hasattr(f["fpgm"], "program") else None
    dropout = "-"
    if prep is not None:
        dropout = "exact" if bytes(prep) == SMART else ("yes" if SMART in bytes(prep) else "no")
    gasp = ",".join("%d:%d" % kv for kv in sorted(f["gasp"].gaspRange.items())) if "gasp" in f else "-"
    lens = ["-" if x is None else str(len(x)) for x in (prep, fpgm)]
    return cls, withcode, n, [dropout] + lens + [gasp], name5

GF = os.environ.get("GF", "/home/fsanches/compartilhado/google/fonts")
seen = set()
print("repo\tfont\tclass\tglyphs_with_instructions\tglyphs\tsmart_dropout\tprep\tfpgm\tgasp\tname5")
for table in sys.argv[1:]:
    for row in csv.DictReader(open(table), delimiter="\t"):
        p = row.get("shipped")
        if p and not os.path.isabs(p):
            p = os.path.join(GF, p)
        if not p or p in seen or not p.endswith(".ttf") or not os.path.exists(p):
            continue
        seen.add(p)
        cls, w, n, extra, n5 = classify(p)
        print("\t".join([row["repo"], os.path.basename(p), cls, str(w), str(n)] + extra + [n5.replace("\t", " ")]))
