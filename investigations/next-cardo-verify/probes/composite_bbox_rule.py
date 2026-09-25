"""composite_bbox_rule.py -- which rule produced each font's glyf HEADER bounding box for
composite glyphs: the control box (all points, on- and off-curve: fontTools/fontc), the
true outline extrema, or the ON-CURVE points only?

Question: the cardo unit leaves ~840 Italic / ~746 Bold base+mark strings unresolved,
where HarfBuzz's fallback mark positioning (it reads glyph extents from the glyf header)
places a mark differently, and names the cause only as "glyf header bounding boxes".
If the release's composite boxes are exactly the on-curve-only extents of the
transformed components, the release is not "stale" but the output of a specific
FontForge rule (quick bounds), and the difference is characterised exactly.

Run: $PY composite_bbox_rule.py <font.ttf> [<font.ttf> ...]
Prints per font: composites whose header equals control box / on-curve box / outline,
and counts of those matching none.
"""
import sys
from collections import Counter
from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib import TTFont

for p in sys.argv[1:]:
    f = TTFont(p); glyf = f["glyf"]; gs = f.getGlyphSet()
    tally = Counter(); ex = {}
    for n in f.getGlyphOrder():
        g = glyf[n]
        if not g.isComposite():
            continue
        coords, end, flags = g.getCoordinates(glyf)
        if not len(coords):
            continue
        hdr = (g.xMin, g.yMin, g.xMax, g.yMax)
        ctrl = (min(x for x, y in coords), min(y for x, y in coords),
                max(x for x, y in coords), max(y for x, y in coords))
        on = [c for c, fl in zip(coords, flags) if fl & 1]
        onb = (min(x for x, y in on), min(y for x, y in on), max(x for x, y in on), max(y for x, y in on))
        bp = BoundsPen(gs); gs[n].draw(bp)
        out = tuple(round(v) for v in bp.bounds)
        k = ("ctrl" if hdr == ctrl else "") + ("on" if hdr == onb else "") + ("outline" if hdr == out else "")
        k = k or "none"
        tally[k] += 1
        ex.setdefault(k, []).append(n)
    print(p.split("/")[-1], dict(tally), {k: v[:6] for k, v in ex.items() if k in ("none", "on")})
