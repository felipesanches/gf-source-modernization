"""Question: how far apart do HarfBuzz's fallback mark positions of a release and a build lie,
over every base (cmap, not a mark) + combining mark (U+0300-036F) pair; and how many of the
release's glyf bounding boxes are stale (header != the outline's control bounds)?
Usage: fallback_mark_delta.py <release.ttf> <build.ttf>"""
import sys
import uharfbuzz as hb
from fontTools.ttLib import TTFont
from fontTools.pens.boundsPen import ControlBoundsPen
rel, bld = sys.argv[1:3]
fa = TTFont(rel)
gs = fa.getGlyphSet()
stale = 0
for g in fa.getGlyphOrder():
    gl = fa["glyf"][g]
    if gl.numberOfContours == 0:
        continue
    p = ControlBoundsPen(gs)
    gs[g].draw(p)
    if p.bounds and tuple(round(x) for x in p.bounds) != (gl.xMin, gl.yMin, gl.xMax, gl.yMax):
        stale += 1
fonts = [hb.Font(hb.Face(hb.Blob.from_file_path(f))) for f in (rel, bld)]
cmap = fa.getBestCmap()
bases = [chr(c) for c in cmap if not 0x300 <= c <= 0x36F and c > 0x20]
marks = [chr(c) for c in range(0x300, 0x370)]
def shape(font, text):
    buf = hb.Buffer(); buf.add_str(text); buf.guess_segment_properties(); hb.shape(font, buf)
    return [(p.x_offset, p.y_offset, p.x_advance) for p in buf.glyph_positions]
n = differ = worst = 0
for b in bases:
    for m in marks:
        n += 1
        ra, rb = shape(fonts[0], b + m), shape(fonts[1], b + m)
        if ra != rb:
            differ += 1
            worst = max(worst, max(abs(x - y) for pa, pb in zip(ra, rb) for x, y in zip(pa, pb)))
print("stale glyf bboxes in the release: %d; base+mark pairs: %d, differ: %d, largest offset difference: %d units"
      % (stale, n, differ, worst))
