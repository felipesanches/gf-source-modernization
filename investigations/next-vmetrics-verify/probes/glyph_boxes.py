#!/usr/bin/env python3
"""Were a release's glyph header boxes written by FontForge's exporter, or recomputed
over all points afterwards (and does the int() rule hold on the release's own outlines)?

Question: for each glyph of the release, is the glyf header yMin/yMax
  (a) FontForge's box: floor/ceil of the source glyph's ON-CURVE SplinePoints (refs
      decomposed; probes/indep_bounds.py's parser), or
  (b) the box over ALL of the release's own stored points (fontTools' recalcBounds)?
Counts glyphs where the header equals (b) but not (a) ("all-point-only") and the
reverse ("ff-only").  Also prints int() of the release outlines' TRUE extremes
(fontTools BoundsPen), which is what googlefontdirectory's tools/bbox/vmetcheck.py
and vmetcorrect.py compute when FontForge opens the .ttf and calls boundingBox().

Run:
  PY=/home/fsanches/compartilhado/gftools/venv/bin/python3
  $PY glyph_boxes.py <file.sfd> <release.ttf>
"""
import math
import os
import sys

from fontTools.pens.boundsPen import BoundsPen

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import indep_bounds as ib  # noqa: E402
from fontTools.ttLib import TTFont  # noqa: E402


def main(sfd, ttf):
    hdr, glyphs, order2 = ib.parse(sfd)
    src = {}
    for pos, g in glyphs.items():
        b = ib.glyph_bounds(ib.flat(glyphs, pos), order2)
        if b:
            src[g['name']] = b
    f = TTFont(ttf)
    glyf = f['glyf']
    gs = f.getGlyphSet()
    allonly, ffonly, both, neither, missing = [], [], [], [], []
    tmax, tmin = (-1e9, None), (1e9, None)
    for name in f.getGlyphOrder():
        g = glyf[name]
        if g.numberOfContours == 0:
            continue
        hy = (g.yMin, g.yMax)
        coords, _, _ = g.getCoordinates(glyf)
        ys = [c[1] for c in coords]
        allp = (min(ys), max(ys))
        bp = BoundsPen(gs)
        gs[name].draw(bp)
        if bp.bounds:
            if bp.bounds[3] > tmax[0]:
                tmax = (bp.bounds[3], name)
            if bp.bounds[1] < tmin[0]:
                tmin = (bp.bounds[1], name)
        s = src.get(name)
        if s is None:
            missing.append(name)
            continue
        ff = (math.floor(s[0][0]), math.ceil(s[0][1]))
        a, b = hy == allp, hy == ff
        (both if a and b else allonly if a else ffonly if b else neither).append(
            (name, hy, allp, ff))
    print(f'release: {ttf}\nsource: {sfd}')
    print(f'  header y-box = all-point box only: {len(allonly)}; = FontForge on-curve box '
          f'only: {len(ffonly)}; both: {len(both)}; neither: {len(neither)}; '
          f'not in source: {len(missing)}')
    for row in allonly[:40]:
        print('   all-point-only', row)
    for row in neither[:20]:
        print('   neither', row)
    print(f"  head yMin/yMax {f['head'].yMin}/{f['head'].yMax}")
    print(f'  release TRUE extremes: max {tmax[0]!r} ({tmax[1]}) -> int {int(tmax[0])}; '
          f'min {tmin[0]!r} ({tmin[1]}) -> int {int(tmin[0])}')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
