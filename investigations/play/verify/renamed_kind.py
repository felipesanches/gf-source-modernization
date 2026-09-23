"""For CHANGED (renamed, not accepted) cmap rows: split into
  adv-or-bbox   advance or bbox differs between release and ours (a real design edit)
  area-only     same advance and bbox, area differs (outline representation or small edit)
Usage: renamed_kind.py <gate.txt> <release.ttf> <ours.ttf>"""
import re, sys
from collections import Counter
from fontTools.ttLib import TTFont
from fontTools.pens.areaPen import AreaPen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import DecomposingRecordingPen
gate, relp, oursp = sys.argv[1:4]
F = [TTFont(relp), TTFont(oursp)]
C = [f.getBestCmap() for f in F]; G = [f.getGlyphSet() for f in F]
def m(i, u):
    g = C[i][u]; b = BoundsPen(G[i]); G[i][g].draw(b); a = AreaPen(G[i]); G[i][g].draw(a)
    p = DecomposingRecordingPen(G[i]); G[i][g].draw(p)
    npts = sum(len(x[1]) for x in p.value); ncont = sum(1 for x in p.value if x[0] == "closePath")
    return F[i]["hmtx"][g][0], tuple(round(x) for x in b.bounds), abs(a.value), npts, ncont
t = Counter()
for line in open(gate):
    mm = re.match(r"\s*BLOCKING cmap U\+([0-9A-F]+)", line)
    if not mm or "LOST" in line: continue
    u = int(mm.group(1), 16); r, o = m(0, u), m(1, u)
    k = "adv-or-bbox" if (r[0] != o[0] or r[1] != o[1]) else "area-only"
    t[k] += 1
    if k == "area-only":
        print(f"U+{u:04X} {C[0][u]}/{C[1][u]} adv {r[0]} bbox {r[1]} area {r[2]:.0f} vs {o[2]:.0f} ({100*(r[2]-o[2])/o[2]:+.2f}%) contours {r[4]}/{o[4]} pts {r[3]}/{o[3]}")
print(dict(t))
