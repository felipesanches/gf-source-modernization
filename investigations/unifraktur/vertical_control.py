#!/usr/bin/env python3
"""What explains the vertical-direction (ttb/btt) runs that still differ once the
shared-script GPOS is grafted? Controls only -- nothing here is a proposed edit.

  A  built + shared GPOS                                   (from empty_gpos_probe.py)
  B  A + hhea.descender -513, usWinDescent 512             (the ff2012 offset base)
  C  B + fsSelection bit 7 (USE_TYPO_METRICS) cleared      (as the OS/2 v3 release)

HarfBuzz synthesises a vertical advance from the horizontal font extents when a
font has no vmtx, and takes those extents from OS/2 typo when bit 7 is set, from
hhea otherwise; so B and C test whether the vertical runs are the metric rows.

    <venv python3> vertical_control.py <release.ttf> <A.ttf> <outdir>
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from empty_gpos_probe import sweep  # noqa: E402
from fontTools.ttLib import TTFont  # noqa: E402

release, a, outdir = sys.argv[1:4]
f = TTFont(a)
f['hhea'].descent = -513
f['OS/2'].usWinDescent = 512
b = os.path.join(outdir, 'B-hhea513.ttf'); f.save(b)
f = TTFont(b)
f['OS/2'].fsSelection &= ~(1 << 7)
c = os.path.join(outdir, 'C-hhea513-nobit7.ttf'); f.save(c)
for label, p in (('A', a), ('B', b), ('C', c)):
    print('release vs %s:' % label, sweep(release, p))
