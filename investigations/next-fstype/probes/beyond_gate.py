#!/usr/bin/env python3
"""beyond_gate.py -- what the table gate does not look at, for one harness run.

Question answered: for each style a tools/baseline.sh run built, against the shipped
binary it was paired with (runs/families-fstype.tsv):
  * cmap   -- codepoints gained / lost (land.py and verify_landed.py require NONE)
  * render -- diffenator3's glyph and word difference counts (d3.json `locations`)
  * names  -- Windows-English name IDs 1, 2, 4, 6, 16, 17 and 5 (the gate leaves the
              name table to disclosure, table_gate.py ACCEPTED['name'])
  * the style-linking bits the gate accepts: fsSelection, macStyle; and
    usWeightClass, fsType, head.fontRevision
Rows marked `!=` are differences; the gate's verdict is in the run's .tsv.

Run (after a run, e.g. r3-extralight with TAG fstype-r3):
  PY=/home/fsanches/compartilhado/gftools/venv/bin/python3
  $PY investigations/next-fstype/probes/beyond_gate.py fstype-r3 [Style...] \
      > investigations/next-fstype/runs/r3-extralight/beyond_gate.txt
The built fonts are read from
  /home/fsanches/compartilhado/sfd-reland-scratch/fstype/baseline/<Style>-<TAG>/
"""
import glob
import json
import os
import sys

from fontTools.ttLib import TTFont

W = "/home/fsanches/compartilhado/gf-source-modernization"
FAM = os.path.join(W, "investigations/next-fstype/runs/families-fstype.tsv")
SCR = "/home/fsanches/compartilhado/sfd-reland-scratch/fstype/baseline"
NAME_IDS = (1, 2, 4, 6, 16, 17, 5)


def rows():
    with open(FAM) as fh:
        head = fh.readline().rstrip("\n").split("\t")
        return [dict(zip(head, l.rstrip("\n").split("\t"))) for l in fh]


def win_name(f, i):
    r = f["name"].getName(i, 3, 1, 0x409)
    return r.toUnicode() if r else None


def main():
    tag, only = sys.argv[1], set(sys.argv[2:])
    for row in rows():
        style = row["style"]
        if only and style not in only:
            continue
        d = "%s/%s-%s" % (SCR, style, tag)
        built = glob.glob(d + "/fonts/ttf/*.ttf")
        print("=" * 80)
        if len(built) != 1:
            print("%s: %d built fonts in %s" % (style, len(built), d))
            continue
        s, b = TTFont(row["shipped"]), TTFont(built[0])
        print("%s  shipped=%s  built=%s" % (style, os.path.basename(row["shipped"]),
                                            os.path.basename(built[0])))
        cs, cb = set(s.getBestCmap()), set(b.getBestCmap())
        print("  cmap gained=%s lost=%s" % (sorted(cb - cs)[:10], sorted(cs - cb)[:10]))
        try:
            j = json.load(open(d + "/d3.json"))
            for loc in j.get("locations", []):
                print("  d3 location %s: glyphs=%d words=%d" % (
                    loc.get("location", "default"), len(loc.get("glyphs") or []),
                    len(loc.get("words") or {})))
        except Exception as e:           # noqa: BLE001
            print("  d3.json unreadable: %s" % e)
        pairs = [("OS/2.fsType", s["OS/2"].fsType, b["OS/2"].fsType),
                 ("OS/2.usWeightClass", s["OS/2"].usWeightClass, b["OS/2"].usWeightClass),
                 ("OS/2.fsSelection", s["OS/2"].fsSelection, b["OS/2"].fsSelection),
                 ("head.macStyle", s["head"].macStyle, b["head"].macStyle),
                 ("head.fontRevision", round(s["head"].fontRevision, 3), round(b["head"].fontRevision, 3))]
        pairs += [("name %d" % i, win_name(s, i), win_name(b, i)) for i in NAME_IDS]
        for k, x, y in pairs:
            print("  %-2s %-20s shipped=%r built=%r" % ("==" if x == y else "!=", k, x, y))


if __name__ == "__main__":
    main()
