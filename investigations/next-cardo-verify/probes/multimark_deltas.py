"""multimark_deltas.py -- for the multi-mark Hebrew corpus of multimark_compare.py, how far
apart (max absolute x/y delta of any glyph) do the release and our build place the
glyphs in each differing string?

Question: are the Bold/Italic multi-mark differences (fonts with no mark feature, so
HarfBuzz fallback-positions the marks from glyf header extents) the same small
header-bbox effect the cardo unit reports for single marks (<=2 units mostly), or larger?

Run: $PY multimark_deltas.py <release.ttf> <built.ttf>
"""
import sys
from collections import Counter
sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
import multimark_compare as mm

S, B = mm.Shaper(sys.argv[1]), mm.Shaper(sys.argv[2])
shared = set(S.cmap) & set(B.cmap)
letters = list(range(0x05D0, 0x05EB)); points = list(range(0x05B0, 0x05BD)) + [0x05C1, 0x05C2, 0x05C7]
cant = list(range(0x0591, 0x05B0))
seqs = [(b, p, c) for b in letters for p in points for c in cant] + \
       [(b, 0x05BC, p, c) for b in letters for p in points if p != 0x05BC for c in cant]
buckets = Counter(); worst = (0, None)
for s in seqs:
    if not all(c in shared for c in s):
        continue
    t = "".join(map(chr, s)); a, b = S.run(t), B.run(t)
    if a == b:
        continue
    if [g for g, _, _ in a] != [g for g, _, _ in b]:
        buckets["glyphs differ"] += 1; continue
    d = max(max(abs(x1 - x2), abs(y1 - y2)) for (_, x1, y1), (_, x2, y2) in zip(a, b))
    buckets["<=2" if d <= 2 else "3..10" if d <= 10 else ">10"] += 1
    if d > worst[0]:
        worst = (d, s)
print(dict(buckets), "worst", worst[0], " ".join("U+%04X" % c for c in (worst[1] or ())))
