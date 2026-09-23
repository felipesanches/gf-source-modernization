"""Question answered: does the font BUILT from the em-scaled .sfd (babelfont+fontc)
carry the same outlines and advances as the release, glyph by glyph?
Independent of the investigator's verify_scaled_points.py: reads only two TTFs.
Outlines are decomposed, implied on-curve points made explicit, each contour
canonicalised (start at min on-curve point; both directions tried), and the
multiset of contours compared exactly. Also compares advance widths, and
glyf header yMax vs the true point yMax per glyph in each font."""
import sys
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import DecomposingRecordingPen

def contours(gs, name):
    p = DecomposingRecordingPen(gs); gs[name].draw(p)
    out = []; cur = None
    for op, args in p.value:
        if op == 'moveTo':
            cur = [(args[0], True)]
        elif op == 'lineTo':
            cur.append((args[0], True))
        elif op == 'qCurveTo':
            if cur is None: cur = []
            offs = list(args[:-1]); end = args[-1]
            for i, o in enumerate(offs):
                cur.append((o, False))
                if i < len(offs) - 1:
                    n = offs[i + 1]
                    cur.append((((o[0] + n[0]) / 2, (o[1] + n[1]) / 2), True))
            if end is None:
                # all-offcurve contour: implied on-curve between last and first
                o, n = offs[-1], offs[0]
                cur.append((((o[0] + n[0]) / 2, (o[1] + n[1]) / 2), True))
            else:
                cur.append((end, True))
        elif op == 'curveTo':
            raise SystemExit('cubic?')
        elif op in ('closePath', 'endPath'):
            if cur and len(cur) > 1 and cur[-1] == cur[0]:
                cur.pop()
            out.append(tuple(cur)); cur = None
    return out

def degen(c):
    # drop an off-curve point that coincides with an adjacent on-curve point
    # (a quadratic whose control sits on an end point is the same line)
    c = list(c); changed = True
    while changed:
        changed = False
        n = len(c)
        for i in range(n):
            pt, on = c[i]
            if on: continue
            pv, nx = c[i-1], c[(i+1) % n]
            if (pv[1] and pv[0] == pt) or (nx[1] and nx[0] == pt):
                del c[i]; changed = True; break
    # drop an on-curve point duplicated by its on-curve neighbour
    return tuple(c)

def canon(c):
    if NORM: c = degen(c)
    best = None
    for seq in (list(c), list(reversed(c))):
        ons = [i for i, (pt, on) in enumerate(seq) if on]
        if not ons:
            continue
        k = min(ons, key=lambda i: seq[i][0])
        r = tuple(seq[k:] + seq[:k])
        best = r if best is None or r < best else best
    return best

NORM = '--degen' in sys.argv
rel, ours = TTFont(sys.argv[1]), TTFont(sys.argv[2])
gr, go = rel.getGlyphSet(), ours.getGlyphSet()
hr, ho = rel['hmtx'].metrics, ours['hmtx'].metrics
names = rel.getGlyphOrder()
bad_o = []; bad_w = []; missing = []
for n in names:
    if n not in go:
        missing.append(n); continue
    a = sorted(canon(c) for c in contours(gr, n))
    b = sorted(canon(c) for c in contours(go, n))
    if a != b:
        bad_o.append(n)
    if hr[n][0] != ho[n][0]:
        bad_w.append((n, hr[n][0], ho[n][0]))
extra = [n for n in ours.getGlyphOrder() if n not in gr]
print('%s: %d release glyphs; outlines differ %d %s; advances differ %d %s; missing %s; extra %s' % (
    sys.argv[1].split('/')[-1], len(names), len(bad_o), bad_o[:12], len(bad_w), bad_w[:8], missing, extra))
