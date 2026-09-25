#!/usr/bin/env python3
"""Question: is the only shaping difference left in Varela-Regular after the babelfont
language-system prototype (shape_langsys.py: 190 of 5,809,820 runs, all the string
"i" + U+0307, advance of .notdef 514 in the release vs 0 in the build, glyphs equal)
caused by the build having NO GPOS table -- the empty-GPOS unit's row -- rather than
by anything in GSUB?

Method: copy the release's (empty) GPOS table into the prototype build and reshape.
If the advance returns to 514, HarfBuzz's fallback mark positioning (which runs only
when a font has no GPOS) was the cause.

Run:
  PY=/home/fsanches/compartilhado/gftools/venv/bin/python3
  $PY varela_residual_gpos.py <release Varela-Regular.ttf> <prototype build .ttf> <scratch .ttf out>
"""
import copy
import sys

import uharfbuzz as hb
from fontTools.ttLib import TTFont


def shape(path, text="i̇"):
    f = hb.Font(hb.Face(hb.Blob.from_file_path(path)))
    order = TTFont(path).getGlyphOrder()
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(f, buf, {})
    return [(order[i.codepoint], p.x_advance) for i, p in zip(buf.glyph_infos, buf.glyph_positions)]


def main():
    rel, bld, out = sys.argv[1:4]
    b = TTFont(bld)
    b["GPOS"] = copy.deepcopy(TTFont(rel)["GPOS"])
    b.save(out)
    for label, p in (("release", rel), ("build", bld), ("build + release's empty GPOS", out)):
        print("%-30s %s" % (label, shape(p)))


if __name__ == "__main__":
    main()
