"""Question: does the gate's geometry tolerance still reject its own negative
control (Allerta vs AllertaStencil, different designs sharing bboxes) when the
contour area is measured with contours split at closePath (the proposed fix)?
Prints, over codepoints with identical advance and bbox edges within 2 units,
the smallest relative |area| difference under the gate's measure and under the
fixed one, and how many would pass 0.4% under each.
Usage: geom_control.py A.ttf B.ttf"""
import sys
sys.path.insert(0, "/home/fsanches/compartilhado/sfd-batch5/tools")
import table_gate as tg
sys.path.insert(0, "/home/fsanches/compartilhado/sfd-reland/investigations/tuffy/probes")
from fontTools.ttLib import TTFont
from fontTools.pens.boundsPen import BoundsPen
A, B = TTFont(sys.argv[1]), TTFont(sys.argv[2])
ca, cb = A.getBestCmap(), B.getBestCmap()
ga, gb = A.getGlyphSet(), B.getGlyphSet()
from fontTools.pens.areaPen import AreaPen
from fontTools.pens.recordingPen import DecomposingRecordingPen
def fixed(gs, n):
    rp = DecomposingRecordingPen(gs); gs[n].draw(rp); t, p = 0.0, AreaPen()
    for op, a in rp.value:
        getattr(p, op)(*a) if a else getattr(p, op)()
        if op in ("closePath", "endPath"): t += abs(p.value); p = AreaPen()
    return t
old, new = [], []
for cp in sorted(set(ca) & set(cb)):
    na, nb = ca[cp], cb[cp]
    if A["hmtx"][na][0] != B["hmtx"][nb][0]: continue
    b1, b2 = BoundsPen(ga), BoundsPen(gb); ga[na].draw(b1); gb[nb].draw(b2)
    if not b1.bounds or not b2.bounds: continue
    if max(abs(x - y) for x, y in zip(b1.bounds, b2.bounds)) > tg._GEOM_BBOX_TOL: continue
    o1, o2 = tg._abs_contour_area(ga, na), tg._abs_contour_area(gb, nb)
    f1, f2 = fixed(ga, na), fixed(gb, nb)
    old.append(abs(o1 - o2) / max(o1, o2, 1.0)); new.append(abs(f1 - f2) / max(f1, f2, 1.0))
print("glyphs with same advance and bbox: %d" % len(old))
print("gate measure : min %.3f%%  pass<=0.4%%: %d" % (100 * min(old), sum(v <= tg._GEOM_AREA_TOL for v in old)))
print("closePath fix: min %.3f%%  pass<=0.4%%: %d" % (100 * min(new), sum(v <= tg._GEOM_AREA_TOL for v in new)))
print("glyphs whose pass/fail differs between the two measures: %d" % sum((a <= tg._GEOM_AREA_TOL) != (b <= tg._GEOM_AREA_TOL) for a, b in zip(old, new)))
print("glyphs whose measured difference changes at all: %d" % sum(abs(a - b) > 1e-12 for a, b in zip(old, new)))
