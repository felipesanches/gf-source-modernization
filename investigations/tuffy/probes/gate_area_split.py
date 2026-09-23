"""Question: are the gate's blocking cmap rename rows real outline differences, or
an artefact of table_gate._abs_contour_area splitting contours only at moveTo?

A TrueType contour made only of off-curve points (implied on-curves) is drawn by
fontTools as qCurveTo(p1, ..., pn, None) + closePath with NO moveTo. The gate's
_abs_contour_area starts a new AreaPen only on moveTo, so such a contour is fed
into the PREVIOUS contour's pen and the per-contour |area| sum is corrupted (e.g.
the counter of Tuffy's Cyrillic a is folded into its outer contour: 23% "area
difference" for two drawings of one shape).

This re-runs the gate's own _same_geometry rule (identical advance, bbox edges
within tg._GEOM_BBOX_TOL, |area| within tg._GEOM_AREA_TOL) with the ONLY change
being contours split at closePath/endPath, and reports each row under both.
Usage: gate_area_split.py release.ttf ours.ttf gate.txt"""
import re, sys
sys.path.insert(0, "/home/fsanches/compartilhado/sfd-batch5/tools")
import table_gate as tg
from fontTools.ttLib import TTFont
from fontTools.pens.areaPen import AreaPen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import DecomposingRecordingPen
def area_fixed(gs, name):
    rp = DecomposingRecordingPen(gs); gs[name].draw(rp)
    total, pen = 0.0, AreaPen()
    for op, args in rp.value:
        getattr(pen, op)(*args) if args else getattr(pen, op)()
        if op in ("closePath", "endPath"):
            total += abs(pen.value); pen = AreaPen()
    return total
def geom(path, cp, fixed):
    f = tg._cached_font(path); n = tg._best_cmap(f)[cp]; gs = f.getGlyphSet()
    bp = BoundsPen(gs); gs[n].draw(bp)
    a = area_fixed(gs, n) if fixed else tg._abs_contour_area(gs, n)
    return f["hmtx"][n][0], bp.bounds, a
def same(R, O, cp, fixed):
    (aa, ab, ar), (ba, bb, br) = geom(R, cp, fixed), geom(O, cp, fixed)
    if aa != ba: return False, "advance %d/%d" % (aa, ba)
    d = max(abs(x - y) for x, y in zip(ab, bb))
    rel = abs(ar - br) / max(ar, br, 1.0)
    return (d <= tg._GEOM_BBOX_TOL and rel <= tg._GEOM_AREA_TOL), "bbox %.1f area %.2f%%" % (d, 100 * rel)
R, O, gate = sys.argv[1:4]
cps = [int(m.group(1), 16) for m in re.finditer(r"^BLOCKING cmap U\+([0-9A-F]+) \[", open(gate).read(), re.M)]
n_old = n_new = 0
for cp in cps:
    try:
        o_ok, o_s = same(R, O, cp, False); f_ok, f_s = same(R, O, cp, True)
    except KeyError:
        print("U+%04X  missing on one side" % cp); continue
    n_old += o_ok; n_new += f_ok
    print("U+%04X  gate-rule: %-5s (%s)   split-at-closePath: %-5s (%s)" % (cp, o_ok, o_s, f_ok, f_s))
print("rows %d: pass under the gate's measure %d; pass with contours split at closePath %d" % (len(cps), n_old, n_new))
