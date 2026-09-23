#!/usr/bin/env python3
"""Question answered: what does the release's missing GSUB change in shaped
text?  Shapes a few E E strings through two fonts and prints glyph names.

Usage: /home/fsanches/compartilhado/gftools/venv/bin/python3 shape_ee.py <release.ttf> <built.ttf>
(the built font is the one tools/baseline.sh leaves in its scratch dir,
 <scratchpad>/baseline/Nosifer-Regular-<TAG>/fonts/ttf/Nosifer-Regular.ttf)
"""
import sys

import uharfbuzz as hb
from fontTools.ttLib import TTFont


def shape(path, text):
    font = hb.Font(hb.Face(hb.Blob.from_file_path(path)))
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(font, buf, {})
    order = TTFont(path).getGlyphOrder()
    return [order[i.codepoint] for i in buf.glyph_infos]


for s in ("BEEF", "SEE", "EEE", "ee"):
    a, b = shape(sys.argv[1], s), shape(sys.argv[2], s)
    print("%-5s release %-24s built %-24s %s" % (s, " ".join(a), " ".join(b), "same" if a == b else "DIFFERENT"))
