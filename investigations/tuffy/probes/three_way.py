"""Question: for every codepoint, which of the three Tuffy binaries agree?
  R = the release google/fonts ships (v1.272, 2017 rebuild)
  F = FontForge's own 2011 export of the same .sfd (v001.271; the monorepo's
      ofl/tuffy/Tuffy-<Style>.ttf, which google/fonts shipped 2015-2017)
  O = our build (babelfont + fontc) of the unmodified .sfd
Comparison is table_gate._same_glyph (advance + canonicalised outline, then the
calibrated quadratic-refit geometry tolerance), i.e. the gate's own comparator.
Prints counts and the codepoints where R differs from F, with glyph names, advance
and bbox on each side.
Usage: three_way.py R.ttf F.ttf O.ttf [cp-hex ...]   (cp list restricts the detail)"""
import sys
sys.path.insert(0, "/home/fsanches/compartilhado/sfd-batch5/tools")
import table_gate as tg
from fontTools.pens.boundsPen import BoundsPen
R, F, O = sys.argv[1:4]
only = {int(x, 16) for x in sys.argv[4:]}
cm = {p: tg._best_cmap(tg._cached_font(p)) for p in (R, F, O)}
def info(p, cp):
    f = tg._cached_font(p); n = cm[p].get(cp)
    if n is None: return None
    gs = f.getGlyphSet(); bp = BoundsPen(gs); gs[n].draw(bp)
    return (n, f["hmtx"][n][0], tuple(int(round(v)) for v in bp.bounds) if bp.bounds else None)
allcp = sorted(set(cm[R]) | set(cm[F]) | set(cm[O]))
rf_diff, of_diff, ro_diff = [], [], []
for cp in allcp:
    rf = cp in cm[R] and cp in cm[F] and tg._same_glyph(R, F, cp)
    of = cp in cm[O] and cp in cm[F] and tg._same_glyph(F, O, cp)
    ro = cp in cm[R] and cp in cm[O] and tg._same_glyph(R, O, cp)
    if not rf: rf_diff.append(cp)
    if not of: of_diff.append(cp)
    if not ro: ro_diff.append(cp)
print("codepoints: R %d  F %d  O %d" % (len(cm[R]), len(cm[F]), len(cm[O])))
print("R!=F: %d   O!=F: %d   R!=O: %d" % (len(rf_diff), len(of_diff), len(ro_diff)))
print("O!=F codepoints:", " ".join("U+%04X" % c for c in of_diff))
for cp in rf_diff:
    if only and cp not in only: continue
    print("U+%04X  R=%s  F=%s  O=%s" % (cp, info(R, cp), info(F, cp), info(O, cp)))
