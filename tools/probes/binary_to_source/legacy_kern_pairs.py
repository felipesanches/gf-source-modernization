#!/usr/bin/env python3
"""Question answered: when a release kerns with a legacy `kern` table and its source now
kerns through a GPOS kern feature, which kerned pairs does HarfBuzz shape differently?

For each shipped font and its build (<scratch>/<stem>/fonts/ttf/*.ttf, as probe.py leaves
them): every pair of every kern subtable whose glyphs are both encoded is shaped through both
fonts (kern on), and the total advances compared. It prints the pairs, how many differ, how
many of those do not involve the soft hyphen (U+00AD), and whether every difference is half
the pair's value -- HarfBuzz applies a legacy kern pair split across the two glyphs and then
hides the default-ignorable soft hyphen, so the half on the hyphen is lost in the release
while the GPOS pair, all on the hyphen, is lost entirely in the build.

Usage: legacy_kern_pairs.py <scratch> <shipped.ttf>...
Measured 2026-10-08 (results/legacy-kern-pairs.txt): Averia Libre, Sans Libre and Serif
Libre, every style: 42 to 102 of 11265 to 16012 pairs differ, all of them with the soft
hyphen, each by half its value; Sansation: 0 of 1097 in every style.
"""
import glob
import os
import sys

import uharfbuzz as hb
from fontTools.ttLib import TTFont


def hbfont(path):
    return hb.Font(hb.Face(hb.Blob.from_file_path(path)))


def advance(font, text):
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(font, buf, {"kern": True})
    return sum(g.x_advance for g in buf.glyph_positions)


def main():
    scratch = sys.argv[1]
    for shipped in sys.argv[2:]:
        stem = os.path.splitext(os.path.basename(shipped))[0]
        built = glob.glob(os.path.join(scratch, stem, "fonts", "ttf", "*.ttf"))[0]
        release = TTFont(shipped)
        cp_of = {}
        for cp, name in release.getBestCmap().items():
            cp_of.setdefault(name, cp)
        fs, fb = hbfont(shipped), hbfont(built)
        pairs, differ = 0, []
        for subtable in release["kern"].kernTables:
            for (left, right), value in subtable.kernTable.items():
                lc, rc = cp_of.get(left), cp_of.get(right)
                if lc is None or rc is None:
                    continue
                pairs += 1
                text = chr(lc) + chr(rc)
                d = advance(fs, text) - advance(fb, text)
                if d:
                    differ.append((left, right, value, d))
        others = [x for x in differ if "uni00AD" not in x[:2]]
        half = all(abs(d) in (abs(int(v / 2)), abs(v) - abs(int(v / 2))) for _, _, v, d in differ)
        print("%-28s pairs %5d differ %3d (not soft hyphen: %d) each by half its value: %s"
              % (stem, pairs, len(differ), len(others), half))


if __name__ == "__main__":
    main()
