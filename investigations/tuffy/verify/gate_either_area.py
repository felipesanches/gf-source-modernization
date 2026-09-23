#!/usr/bin/env python3
"""Adversarial verification, unit "tuffy".
Question it answers: if the gate's geometry test accepted a glyph when EITHER the
per-contour |area| sum (current measure) OR the filled-region area (skia-pathops,
nonzero) agrees within 0.4% -- advance and bbox tests unchanged -- which rows close,
and does any row open? Overlap removal changes the first measure, not the second.
Usage: gate_either_area.py <d3.json> --fonts <shipped> <built>
       gate_either_area.py --control <A.ttf> <B.ttf>   (Allerta negative control)"""
import sys
sys.path.insert(0, "/home/fsanches/compartilhado/sfd-batch5/tools")
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import table_gate as tg
from gate_filled_area import filled_area  # noqa: E402  (module guards its own main)

_orig = tg._same_geometry


def _either(shipped, built, cp):
    if _orig(shipped, built, cp):
        return True
    saved = tg._abs_contour_area
    tg._abs_contour_area = filled_area
    try:
        return _orig(shipped, built, cp)
    finally:
        tg._abs_contour_area = saved


if sys.argv[1] == "--control":
    from fontTools.ttLib import TTFont
    from fontTools.pens.boundsPen import BoundsPen
    A, B = sys.argv[2], sys.argv[3]
    ca, cb = TTFont(A).getBestCmap(), TTFont(B).getBestCmap()
    n = a = b = 0
    for cp in sorted(set(ca) & set(cb)):
        x, y = _orig(A, B, cp), _either(A, B, cp)
        n += 1; a += x; b += y
    print("control: %d shared codepoints; same-geometry verdicts: gate %d, either-measure %d" % (n, a, b))
    sys.exit(0)
tg._same_geometry = _either
sys.argv = [tg.__file__] + sys.argv[1:]
tg.main()
