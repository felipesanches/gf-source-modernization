#!/usr/bin/env python3
"""colinear_emulate.py -- why does fontspector's outline_colinear_vectors WARN on the
shipped Wallpoet and PASS on our build?

Question answered: emulating fontspector 1.6.0 profile-googlefonts
checks/outline/colinear_vectors.rs (consecutive kurbo Line segments, circularly, whose
atan2 angles differ by < 0.1 rad; returns PASS as soon as MORE THAN 100 hits are
collected), how many hits does each font give, per glyph, drawn (a) from the glyf
points as stored and (b) through fontTools' pen (implied on-curve points expanded)?
A PASS reached through the >100 early return is not evidence of cleaner outlines.

Run: $PY colinear_emulate.py <shipped.ttf> <built.ttf>
"""
import math
import sys
from collections import Counter

from fontTools.pens.basePen import BasePen
from fontTools.ttLib import TTFont


class SegPen(BasePen):
    """Records kurbo-like segments: Line or Curve, closing Line added when needed."""
    def __init__(self, gs):
        super().__init__(gs)
        self.contours, self.cur, self.start, self.pt = [], [], None, None

    def _moveTo(self, p):
        self.cur, self.start, self.pt = [], p, p

    def _lineTo(self, p):
        self.cur.append(("L", self.pt, p)); self.pt = p

    def _qCurveToOne(self, p1, p2):
        self.cur.append(("Q", self.pt, p2)); self.pt = p2

    def _curveToOne(self, p1, p2, p3):
        self.cur.append(("C", self.pt, p3)); self.pt = p3

    def _closePath(self):
        if self.pt != self.start:
            self.cur.append(("L", self.pt, self.start))
        self.contours.append(self.cur)

    _endPath = _closePath


def hits(font):
    gs = font.getGlyphSet()
    c = Counter()
    for name in font.getGlyphOrder():
        pen = SegPen(gs)
        gs[name].draw(pen)
        for segs in pen.contours:
            n = len(segs)
            for i in range(n):
                a, b = segs[i], segs[(i + 1) % n]
                if a[0] == "L" and b[0] == "L":
                    pa = math.atan2(a[2][1] - a[1][1], a[2][0] - a[1][0])
                    pb = math.atan2(b[2][1] - b[1][1], b[2][0] - b[1][0])
                    if abs(pa - pb) < 0.1:
                        c[name] += 1
    return c


for path in sys.argv[1:3]:
    c = hits(TTFont(path))
    print("%s: %d hits; %s" % (path.split("/")[-1], sum(c.values()), c.most_common(12)))
