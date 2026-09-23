"""For every BLOCKING cmap row of a gate transcript: is the glyph at that codepoint in
the release (v2.101) the same design as in the hg-era v1.002 binary (FontForge export)
and as in our build? Compares decomposed outlines as sets of on/off points after
rounding (start point / contour order ignored), plus advance.
Verdict per row:
  v2-change      release != v1.002 and ours == v1.002  -> design changed after v1 (provenance)
  conv-suspect   release == v1.002 and ours != v1.002  -> our conversion differs from FontForge (fidelity!)
  both-differ    release != v1.002 and ours != v1.002
  absent-v1      codepoint not in v1.002
Usage: threeway.py <gate.txt> <release.ttf> <v1.ttf> <ours.ttf>"""
import re, sys
from collections import Counter
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.areaPen import AreaPen
from fontTools.pens.boundsPen import BoundsPen

gate, relp, v1p, oursp = sys.argv[1:5]
fonts = {k: TTFont(p) for k, p in [("rel", relp), ("v1", v1p), ("ours", oursp)]}
cm = {k: f.getBestCmap() for k, f in fonts.items()}
gs = {k: f.getGlyphSet() for k, f in fonts.items()}

def sig(k, u):
    g = cm[k].get(u)
    if g is None:
        return None
    p = DecomposingRecordingPen(gs[k]); gs[k][g].draw(p)
    pts = Counter()
    for op, args in p.value:
        for a in args:
            pts[(round(a[0]), round(a[1]))] += 1
    bp = BoundsPen(gs[k]); gs[k][g].draw(bp)
    ap = AreaPen(gs[k]); gs[k][g].draw(ap)
    return (fonts[k]["hmtx"][g][0], bp.bounds and tuple(round(x) for x in bp.bounds), round(abs(ap.value)), pts)

def same(a, b, loose=False):
    if a is None or b is None:
        return a is b
    if a[0] != b[0]:
        return False
    if a[3] == b[3]:
        return True
    if loose:  # bbox within 1 and area within 0.2%
        return a[1] == b[1] and abs(a[2]-b[2]) <= 0.002*max(a[2], b[2], 1)
    return False

tally = Counter(); rows = []
for line in open(gate):
    m = re.match(r"\s*BLOCKING cmap U\+([0-9A-F]+)\s+(\S+)?", line)
    if not m:
        continue
    u = int(m.group(1), 16); lost = "LOST" in line
    r, v, o = sig("rel", u), sig("v1", u), sig("ours", u)
    if v is None:
        verdict = "absent-v1" + ("-and-ours" if o is None else "")
    elif same(r, v, True) and not same(o, v, True):
        verdict = "conv-suspect"
    elif not same(r, v, True) and same(o, v, True):
        verdict = "v2-change"
    elif same(r, v, True) and same(o, v, True):
        verdict = "all-same?"
    else:
        verdict = "both-differ"
    tally[("LOST" if lost else "CHANGED", verdict)] += 1
    rows.append((f"U+{u:04X}", "LOST" if lost else "CHANGED", verdict,
                 cm["rel"].get(u), r and r[:3], cm["v1"].get(u), v and v[:3], cm["ours"].get(u), o and o[:3]))
for row in rows:
    if row[2] not in ("v2-change", "absent-v1-and-ours"):
        print("\t".join(map(str, row)))
print("TALLY", dict(tally))
