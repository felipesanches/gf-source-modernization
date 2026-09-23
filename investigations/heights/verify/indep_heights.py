#!/usr/bin/env python3
"""Independent check of FontForge's SFStandardHeight, measured on a BINARY's
outlines (glyf or CFF) through fontTools, not on the .sfd.

Rule (splinefont.c SFStandardHeight, b69c9652 / 5a11aa4c): for each code point of
the fixed list, the glyph's top = the highest y of its outline (refs decomposed);
it is FLAT when a horizontal straight segment lies exactly at that top (FontForge's
>= tie rule makes a flat win any tie), otherwise it is a curve/pointy top.
  any flat top -> the mode of the flat tops (ties averaged)
  else         -> sum of DISTINCT curve tops / divisor
                   2011 (b69c9652): divisor = number of glyphs with a curve top
                   2012 (4d34d21e+): divisor = number of distinct curve tops
then snap to a BlueValues zone bottom within (ascent+descent)/100, truncate.

Exact arithmetic (Fractions) for extrema; a straight test is geometric: every
control point on the chord and inside its span.

usage: indep_heights.py <font.ttf|otf> [--blues "a b c d"] [--em N]
"""
import sys
from fractions import Fraction as F
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import DecomposingRecordingPen

R = None
CAP = [0x41, R, 0x5A, 0x391, R, 0x3A9, 0x402, 0x404, 0x405, 0x406, 0x408, R, 0x40B,
       0x40F, R, 0x418, 0x41A, 0x42F]
XH = [ord(c) for c in "acegmnopqrsuvwxyz"] + [0x131, 0x3B3, 0x3B9, 0x3BA, 0x3BC, 0x3BD,
      0x3C0, 0x3C3, 0x3C4, 0x3C5, 0x3C7, 0x3C8, 0x3C9, 0x432, 0x433, 0x438, 0x43A, R,
      0x43F, 0x442, 0x443, 0x445, 0x44C, 0x44F, 0x459, 0x45A]


def codepoints(lst):
    out, i = [], 0
    while i < len(lst):
        lo = hi = lst[i]
        if i + 2 < len(lst) and lst[i + 1] is R:
            hi = lst[i + 2]
            i += 2
        out += list(range(lo, hi + 1))
        i += 1
    return out


def segs_of(recording):
    """Yield (kind, points) with points as Fractions; kind in line/quad/cubic."""
    cur = start = None
    for op, args in recording:
        if op == "moveTo":
            cur = start = tuple(F(v) for v in args[0])
        elif op == "lineTo":
            p = tuple(F(v) for v in args[0])
            yield "line", (cur, p)
            cur = p
        elif op == "qCurveTo":
            pts = [tuple(F(v) for v in a) for a in args]
            if pts[-1] is None:
                raise SystemExit("implied-oncurve contour not handled")
            offs, end = pts[:-1], pts[-1]
            for k, c in enumerate(offs):
                nxt = end if k == len(offs) - 1 else ((c[0] + offs[k + 1][0]) / 2, (c[1] + offs[k + 1][1]) / 2)
                yield "quad", (cur, c, nxt)
                cur = nxt
        elif op == "curveTo":
            pts = [tuple(F(v) for v in a) for a in args]
            yield "cubic", (cur, pts[0], pts[1], pts[2])
            cur = pts[2]
        elif op in ("closePath", "endPath"):
            if cur is not None and start is not None and cur != start:
                yield "line", (cur, start)
            cur = start = None


def on_chord(p0, p3, c):
    # collinear and within the span of the chord
    cross = (p3[0] - p0[0]) * (c[1] - p0[1]) - (p3[1] - p0[1]) * (c[0] - p0[0])
    if cross != 0:
        return False
    return (min(p0[0], p3[0]) <= c[0] <= max(p0[0], p3[0]) and
            min(p0[1], p3[1]) <= c[1] <= max(p0[1], p3[1]))


def seg_top(kind, pts):
    """(max y, straight?)"""
    ys = [p[1] for p in pts]
    p0, p3 = pts[0], pts[-1]
    if kind == "line" or all(on_chord(p0, p3, c) for c in pts[1:-1]):
        return max(p0[1], p3[1]), True, p0[1] == p3[1]
    m = max(p0[1], p3[1])
    if kind == "quad":
        a = p0[1] - 2 * pts[1][1] + p3[1]
        if a != 0:
            t = (p0[1] - pts[1][1]) / a
            if 0 < t < 1:
                y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * pts[1][1] + t * t * p3[1]
                m = max(m, y)
    else:
        y0, y1, y2, y3 = ys
        # derivative: 3[(y1-y0)(1-t)^2 + 2(y2-y1)(1-t)t + (y3-y2)t^2]
        A = (y1 - y0) - 2 * (y2 - y1) + (y3 - y2)
        B = 2 * ((y2 - y1) - (y1 - y0))
        C = (y1 - y0)
        roots = []
        if A == 0:
            if B != 0:
                roots = [-C / B]
        else:
            disc = B * B - 4 * A * C
            if disc >= 0:
                import math
                s = F(math.sqrt(float(disc)))  # float sqrt; tie risk flagged below
                roots = [(-B - s) / (2 * A), (-B + s) / (2 * A)]
        for t in roots:
            if 0 < t < 1:
                y = (1 - t) ** 3 * y0 + 3 * (1 - t) ** 2 * t * y1 + 3 * (1 - t) * t * t * y2 + t ** 3 * y3
                m = max(m, y)
    return m, False, False


def glyph_top(gs, name):
    pen = DecomposingRecordingPen(gs)
    gs[name].draw(pen)
    top, flat, any_seg = None, False, False
    tops = []
    for kind, pts in segs_of(pen.value):
        any_seg = True
        m, straight, horiz = seg_top(kind, pts)
        tops.append((m, straight and horiz))
    if not any_seg:
        return None, None
    top = max(m for m, _ in tops)
    flat = any(h and m == top for m, h in tops)
    return top, flat


def standard(font, lst, blues, em, trace):
    cmap = font.getBestCmap()
    gs = font.getGlyphSet()
    flats, curves = {}, {}
    for cp in codepoints(lst):
        n = cmap.get(cp)
        if n is None:
            continue
        top, flat = glyph_top(gs, n)
        if top is None:
            continue
        trace.append((cp, n, float(top), "flat" if flat else "curve"))
        d = flats if flat else curves
        d[top] = d.get(top, 0) + 1
    res = {}
    if flats:
        mx = max(flats.values())
        tied = [p for p, c in flats.items() if c == mx]
        res["2011"] = res["2012"] = sum(tied) / len(tied)
    elif curves:
        s = sum(curves)
        res["2011"] = s / sum(curves.values())
        res["2012"] = s / len(curves)
    else:
        return None, flats, curves
    out = {}
    for k, v in res.items():
        r = v
        if blues:
            best, bd = v, F(em) / 100
            for z in blues[0::2]:
                if abs(z - v) < bd:
                    best, bd = F(z), abs(z - v)
            r = best
        out[k] = (float(v), int(r) if r >= 0 else 0)
    return out, flats, curves


def main():
    path = sys.argv[1]
    blues = None
    em = None
    if "--blues" in sys.argv:
        blues = [F(x) for x in sys.argv[sys.argv.index("--blues") + 1].split()]
    font = TTFont(path)
    em = int(sys.argv[sys.argv.index("--em") + 1]) if "--em" in sys.argv else font["head"].unitsPerEm
    for label, lst in (("x-height", XH), ("cap height", CAP)):
        tr = []
        out, flats, curves = standard(font, lst, blues, em, tr)
        print("== %s" % label)
        for cp, n, t, k in tr:
            print("  U+%04X %-16s %-5s %.6f" % (cp, n, k, t))
        print("  flats  %s" % sorted((float(p), c) for p, c in flats.items()))
        print("  curves %s" % sorted((float(p), c) for p, c in curves.items()))
        if curves and not flats:
            print("  curve sum %.6f  glyphs %d  distinct %d" % (float(sum(curves)), sum(curves.values()), len(curves)))
        print("  RESULT 2011=%s 2012=%s" % (out and out["2011"], out and out["2012"]))


if __name__ == "__main__":
    main()
