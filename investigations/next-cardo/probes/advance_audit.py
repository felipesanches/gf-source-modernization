#!/usr/bin/env python3
"""Does the table gate hide advance-width differences?

Question answered: for a shipped/built pair, which glyphs have a different ADVANCE
(hmtx width), and would table_gate.py (sfd-batch5 2f43693) have reported each one?

Two gate paths drop an advance difference without saying so:
  1. diffenator3 replaces a large hmtx section with
     {"error": "There are N changes, check manually!"}; expand_overflow() then
     recomputes LEFT SIDE BEARINGS only and never looks at advances.
  2. arbitrate_lsb() reclassifies a whole hmtx row as RELEASE-STALE when the
     release's bearing contradicts its own outline, even when the same row also
     carries a "width" difference (its `'"advance"' not in row` guard looks for a key
     diffenator3 never writes; the key is "width").
This probe recomputes every advance directly and marks each difference as
  REPORTED  the gate printed a BLOCKING hmtx row for it
  HIDDEN    it did not (path 1 or 2 above)
Glyphs are paired by name (both fonts keep source glyph names here); a glyph present
on one side only is skipped (the gate's rename class).

Usage:
  advance_audit.py <shipped.ttf> <built.ttf> [<gate.txt> [<d3.json>]]
  advance_audit.py --scan <scratch-root> <families.tsv> <dir-suffix>
      every <scratch-root>/<Style><dir-suffix>/ holding fonts/ttf/*.ttf and d3.json,
      paired with the shipped font the pairing table names for <Style>; the gate is
      re-run on the saved d3.json to decide REPORTED/HIDDEN.
Prints one line per differing glyph: style, glyph, shipped advance, built advance,
REPORTED|HIDDEN, and the path that hid it.
Python: /home/fsanches/compartilhado/gftools/venv/bin/python3
"""
import glob
import json
import os
import subprocess
import sys

from fontTools.ttLib import TTFont

TG = "/home/fsanches/compartilhado/sfd-batch5/tools/table_gate.py"
PY = "/home/fsanches/compartilhado/gftools/venv/bin/python3"


def advances(path):
    f = TTFont(path)
    return {n: f["hmtx"][n][0] for n in f.getGlyphOrder()}


def gate_rows(d3json, shipped, built):
    p = subprocess.run([PY, TG, d3json, "--fonts", shipped, built],
                       capture_output=True, text=True)
    return p.stdout


def audit(style, shipped, built, gate_text, d3json=None):
    s, b = advances(shipped), advances(built)
    overflow = False
    if d3json and os.path.exists(d3json):
        try:
            h = (json.load(open(d3json)).get("tables") or {}).get("hmtx") or {}
        except ValueError:
            h = {}                      # an empty d3.json: diffenator3 did not finish
        overflow = "error" in h
    out = []
    for n in s:
        if n not in b or s[n] == b[n]:
            continue
        blocking = "BLOCKING hmtx.%s " % n in gate_text
        stale = "RELEASE-STALE hmtx.%s " % n in gate_text
        if blocking:
            how = "REPORTED"
            why = ""
        else:
            how = "HIDDEN"
            why = ("lsb-arbitration" if stale else
                   "d3-overflow" if overflow else "not-in-gate")
        out.append("%s\t%s\t%d\t%d\t%s\t%s" % (style, n, s[n], b[n], how, why))
    return out


def rows(path):
    with open(path, encoding="utf-8") as fh:
        head = fh.readline().rstrip("\n").split("\t")
        return [dict(zip(head, l.rstrip("\n").split("\t"))) for l in fh if l.strip()]


def main():
    a = sys.argv[1:]
    if a and a[0] == "--scan":
        root, fam, suffix = a[1], a[2], a[3]
        shipped = {r["style"]: r["shipped"] for r in rows(fam)}
        for d in sorted(glob.glob(os.path.join(root, "*" + suffix))):
            style = os.path.basename(d)[:-len(suffix)]
            built = glob.glob(os.path.join(d, "fonts/ttf/*.ttf"))
            d3 = os.path.join(d, "d3.json")
            if style not in shipped or len(built) != 1 or not os.path.exists(d3) \
                    or os.path.getsize(d3) == 0:
                continue
            gate = gate_rows(d3, shipped[style], built[0])
            for line in audit(style, shipped[style], built[0], gate, d3):
                print(line)
        return
    shipped, built = a[0], a[1]
    gate = open(a[2]).read() if len(a) > 2 else ""
    d3 = a[3] if len(a) > 3 else None
    for line in audit(os.path.basename(shipped), shipped, built, gate, d3):
        print(line)


if __name__ == "__main__":
    main()
