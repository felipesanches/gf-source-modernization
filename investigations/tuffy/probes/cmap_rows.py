"""Question: for each BLOCKING cmap rename row of the baseline gate, what differs
between the release and our build, and does removing overlaps from our glyph
(skia-pathops, as the release's toolchain did on export) make them agree?
Per codepoint prints advance (release/ours), max bbox-edge delta, relative
|contour| area difference, then the same two measures after overlap removal of
OUR glyph, and whether table_gate's geometry test (_GEOM_BBOX_TOL 2 units,
_GEOM_AREA_TOL 0.4%) would then pass.
Usage: cmap_rows.py release.ttf ours.ttf gate.txt"""
import re, sys, copy
sys.path.insert(0, "/home/fsanches/compartilhado/sfd-batch5/tools")
import table_gate as tg
from fontTools.ttLib import TTFont
from fontTools.ttLib.removeOverlaps import removeOverlaps
from fontTools.pens.boundsPen import BoundsPen
R, O, gate = sys.argv[1:4]
fr, fo = TTFont(R), TTFont(O)
fo2 = TTFont(O)
cps = [int(m.group(1), 16) for m in re.finditer(r"^BLOCKING cmap U\+([0-9A-F]+) \[", open(gate).read(), re.M)]
cr, co = fr.getBestCmap(), fo.getBestCmap()
removeOverlaps(fo2, [co[c] for c in cps if c in co] + [c.glyphName for c in []], removeHinting=True)
def geo(f, n):
    gs = f.getGlyphSet(); bp = BoundsPen(gs); gs[n].draw(bp)
    return f["hmtx"][n][0], bp.bounds, tg._abs_contour_area(gs, n)
npass = 0
for cp in cps:
    if cp not in cr or cp not in co:
        print("U+%04X only in %s" % (cp, "release" if cp in cr else "ours")); continue
    a = geo(fr, cr[cp]); b = geo(fo, co[cp])
    fo2g = fo2["glyf"][co[cp]]
    c = geo(fo2, co[cp])
    def d(x, y):
        bb = max(abs(p - q) for p, q in zip(x[1], y[1])) if x[1] and y[1] else None
        ar = abs(x[2] - y[2]) / max(x[2], y[2], 1.0)
        return bb, round(100 * ar, 2)
    bb1, ar1 = d(a, b); bb2, ar2 = d(a, c)
    ok = a[0] == c[0] and bb2 is not None and bb2 <= tg._GEOM_BBOX_TOL and ar2 <= 100 * tg._GEOM_AREA_TOL
    npass += ok
    print("U+%04X %-24s adv %4d/%4d  bbox-delta %4s area %6.2f%%  | overlaps removed: bbox-delta %4s area %6.2f%%  %s"
          % (cp, "%s/%s" % (cr[cp], co[cp]), a[0], b[0], bb1, ar1, bb2, ar2, "GEOM-PASS" if ok else "differs"))
print("rows:", len(cps), " pass after overlap removal of ours:", npass)
