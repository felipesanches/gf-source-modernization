#!/usr/bin/env python3
"""Is a release's head.fontDirectionHint the value FontForge's pre-2019 exporter computed?

Question answered: for every style of a pairing table, does the shipped font's
fontDirectionHint equal what FontForge's tottf.c wrote before commit 722e7ea8873e
("Skip Apple 'head' table fields in OpenType mode", 2017-12-23; first release
20190317)? That code, identical in tags v20110222 .. 20170731, is

    lr = rl = 0;  for each exported glyph:
        if SCRightToLeft(sc) rl = 1;
        else if (uni < 0x10000 && islefttoright(uni)) || 0x10300 <= uni < 0x107ff: lr = 1;
    dirhint = (lr && rl) ? 0 : rl ? -2 : 2;   and head.flags bit 9 is set when rl

and from 20190317 on, in OpenType mode, dirhint = 2 unconditionally (fontc and
ufo2ft/fontmake also write 2; the OpenType spec says "Deprecated (Set to 2)").
The oracle approximates FontForge's islefttoright/isrighttoleft with Python's
unicodedata.bidirectional over the release's cmap (L -> lr; R or AL -> rl).

It also reports the release's FFTM build stamp and head.flags bit 9, so a gate rule
can check that a non-2 value is FontForge's own, internally consistent, output.

Usage:
  FAMILIES=<pairing.tsv> dirhint_oracle.py      (default: sfd-reland/families-next.tsv)
Prints: style, shipped dirhint, oracle dirhint, MATCH|DIFF, head.flags bit 9, FFTM date.
Python: /home/fsanches/compartilhado/gftools/venv/bin/python3
"""
import datetime
import os
import unicodedata

from fontTools.ttLib import TTFont

UNIX_FROM_1904 = 2082844800


def oracle(font):
    lr = rl = False
    for cp in (font.getBestCmap() or {}):
        bidi = unicodedata.bidirectional(chr(cp))
        if bidi in ("R", "AL") or 0x10800 <= cp <= 0x10FFF:
            rl = True
        elif (cp < 0x10000 and bidi == "L") or 0x10300 <= cp < 0x107FF:
            lr = True
    return 0 if (lr and rl) else -2 if rl else 2


def rows(path):
    with open(path, encoding="utf-8") as fh:
        head = fh.readline().rstrip("\n").split("\t")
        return [dict(zip(head, l.rstrip("\n").split("\t"))) for l in fh if l.strip()]


def main():
    fam = os.environ.get("FAMILIES", "/home/fsanches/compartilhado/sfd-reland/families-next.tsv")
    for r in rows(fam):
        p = r["shipped"]
        if not os.path.exists(p):
            continue
        f = TTFont(p)
        shipped = f["head"].fontDirectionHint
        o = oracle(f)
        bit9 = (f["head"].flags >> 9) & 1
        stamp = "-"
        if "FFTM" in f:
            stamp = datetime.datetime.fromtimestamp(
                f["FFTM"].FFTimeStamp - UNIX_FROM_1904, datetime.UTC).date().isoformat()
        print("%s\t%d\t%d\t%s\tbit9=%d\tFFTM=%s" % (r["style"], shipped, o,
              "MATCH" if shipped == o else "DIFF", bit9, stamp))


if __name__ == "__main__":
    main()
