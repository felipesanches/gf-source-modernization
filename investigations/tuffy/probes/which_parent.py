"""Question: which 2011 artefact did the 2017 v1.272 release start from -- the
FontForge TTF export (v001.271, quadratic, in the monorepo beside the .sfd) or
the CFF .otf (v001.270, cubic, monorepo src/)? For every codepoint all three
carry, compares the release's glyph bbox and advance with each candidate's, and
counts exact-bbox agreement; also counts glyphs whose ON-CURVE point set in the
release equals the candidate's on-curve set (the TTF), or contains all of the
candidate's on-curve points (the OTF).
Usage: which_parent.py release.ttf ff_export.ttf source.otf"""
import sys
from fontTools.ttLib import TTFont
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import DecomposingRecordingPen
R, T, C = (TTFont(p) for p in sys.argv[1:4])
def bbox(f, n):
    gs = f.getGlyphSet(); bp = BoundsPen(gs); gs[n].draw(bp)
    return tuple(round(v) for v in bp.bounds) if bp.bounds else None
def oncurve(f, n):
    gs = f.getGlyphSet(); rp = DecomposingRecordingPen(gs); gs[n].draw(rp); pts = set()
    for op, args in rp.value:
        if op in ("moveTo", "lineTo"): pts.add(tuple(round(v) for v in args[0]))
        elif op in ("curveTo", "qCurveTo") and args[-1] is not None: pts.add(tuple(round(v) for v in args[-1]))
    return pts
cr, ct, cc = R.getBestCmap(), T.getBestCmap(), C.getBestCmap()
cps = sorted(set(cr) & set(ct) & set(cc))
bt = bc = ot = oc = 0; only_c = []; only_t = []
for cp in cps:
    b = bbox(R, cr[cp]); x = bbox(T, ct[cp]) == b; y = bbox(C, cc[cp]) == b
    bt += x; bc += y
    if y and not x: only_c.append(cp)
    if x and not y: only_t.append(cp)
    orr = oncurve(R, cr[cp]); ot += orr == oncurve(T, ct[cp]); oc += oncurve(C, cc[cp]) <= orr
print("shared codepoints:", len(cps))
print("release bbox == TTF 001.271 bbox:", bt, "   == OTF 001.270 bbox:", bc)
print("release on-curve set == TTF's:", ot, "   release on-curve set contains all OTF on-curve points:", oc)
print("bbox matches OTF only:", " ".join("U+%04X" % c for c in only_c[:40]))
print("bbox matches TTF only:", " ".join("U+%04X" % c for c in only_t[:40]))
