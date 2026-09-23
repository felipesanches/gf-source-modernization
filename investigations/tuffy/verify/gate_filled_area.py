#!/usr/bin/env python3
"""Adversarial verification, unit "tuffy".
Question it answers: which gate rows are only overlap representation? Runs the
unmodified sfd-batch5/tools/table_gate.py main() with _abs_contour_area replaced
by the area of the FILLED region (skia-pathops simplify under the nonzero rule,
i.e. what a rasteriser fills). Removing overlaps leaves the filled region unchanged,
so a row that closes here and not under the gate's per-contour sum is a
representation difference (overlap removed), not a drawing difference.
Also: --control A.ttf B.ttf prints how many of the codepoints sharing advance and
bbox pass 0.4% under each measure (Allerta vs AllertaStencil negative control).
Usage: gate_filled_area.py <d3.json> --fonts <shipped> <built>
       gate_filled_area.py --control <A.ttf> <B.ttf>"""
import sys
sys.path.insert(0, "/home/fsanches/compartilhado/sfd-batch5/tools")
import table_gate as tg
import pathops
from fontTools.pens.areaPen import AreaPen


def filled_area(glyphs, name):
    p = pathops.Path()
    glyphs[name].draw(p.getPen(glyphSet=glyphs))
    p.simplify(fix_winding=True)
    total = 0.0
    for c in p.contours:          # simplified: disjoint outers + holes, consistent winding
        ap = AreaPen()
        c.draw(ap)
        total += ap.value
    return abs(total)


def _main():
  if sys.argv[1] == "--control":
      from fontTools.ttLib import TTFont
      from fontTools.pens.boundsPen import BoundsPen
      A, B = TTFont(sys.argv[2]), TTFont(sys.argv[3])
      ca, cb = A.getBestCmap(), B.getBestCmap()
      ga, gb = A.getGlyphSet(), B.getGlyphSet()
      n = po = pf = ch = 0
      for cp in sorted(set(ca) & set(cb)):
          na, nb = ca[cp], cb[cp]
          if A["hmtx"][na][0] != B["hmtx"][nb][0]:
              continue
          b1, b2 = BoundsPen(ga), BoundsPen(gb)
          ga[na].draw(b1); gb[nb].draw(b2)
          if not b1.bounds or not b2.bounds:
              continue
          if max(abs(x - y) for x, y in zip(b1.bounds, b2.bounds)) > tg._GEOM_BBOX_TOL:
              continue
          o1, o2 = tg._abs_contour_area(ga, na), tg._abs_contour_area(gb, nb)
          f1, f2 = filled_area(ga, na), filled_area(gb, nb)
          a = abs(o1 - o2) / max(o1, o2, 1.0) <= tg._GEOM_AREA_TOL
          b = abs(f1 - f2) / max(f1, f2, 1.0) <= tg._GEOM_AREA_TOL
          n += 1; po += a; pf += b; ch += (a != b)
      print("control: %d codepoints share advance+bbox; pass 0.4%%: gate measure %d, filled-region %d; verdicts changed %d" % (n, po, pf, ch))
      sys.exit(0)
  tg._abs_contour_area = filled_area
  sys.argv = [tg.__file__] + sys.argv[1:]
  tg.main()


if __name__ == "__main__":
    _main()
