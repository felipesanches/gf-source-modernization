#!/usr/bin/env python3
"""Question answered: for each instructed glyph whose built points are not the release's, what
makes them differ? Classes, tried in order (the first that explains it):
  implied   the build lacks on-curve points halfway between two off-curves (fontc drops them)
  repeated  the build lacks a point repeating the one before it, or a one-point contour
  start     the same points from another start
  shift     the same points moved horizontally
  several   a combination of the above
  other     none of these (the outline differs)
Usage: why_points_differ.py <release.ttf> <built.ttf>   -> counts per class
"""
import collections
import sys

from fontTools.ttLib import TTFont


def contours(g):
    if g.numberOfContours <= 0:
        return []
    out, s = [], 0
    for e in g.endPtsOfContours:
        out.append([(x, y, g.flags[i] & 1) for i, (x, y) in enumerate(g.coordinates[s:e + 1], s)])
        s = e + 1
    return out


def no_implied(c):
    n = len(c)
    return [p for i, p in enumerate(c) if not (p[2] and not c[i - 1][2] and not c[(i + 1) % n][2]
            and c[i - 1][0] + c[(i + 1) % n][0] == 2 * p[0] and c[i - 1][1] + c[(i + 1) % n][1] == 2 * p[1])]


def no_repeated(cs):
    cs = [[p for i, p in enumerate(c) if len(c) == 1 or p != c[i - 1]] for c in cs]
    return [c for c in cs if len(c) > 1]


def rot_eq(a, b):
    return len(a) == len(b) and (not a or any(b[i:] + b[:i] == a for i in range(len(b))))


def shifted(cs, dx):
    return [[(x + dx, y, o) for x, y, o in c] for c in cs]


def classify(a, b):
    A, B = contours(a), contours(b)
    if A == B:
        return None
    def eq(f, g, rot=False):
        if len(f) != len(g):
            return False
        return all((rot_eq(x, y) if rot else x == y) for x, y in zip(f, g))
    xa = [x for c in A for x, _, _ in c]
    xb = [x for c in B for x, _, _ in c]
    dx = (min(xa) - min(xb)) if xa and xb else 0
    single = {
        "implied": eq([no_implied(c) for c in A], [no_implied(c) for c in B]),
        "repeated": eq(no_repeated(A), no_repeated(B)),
        "start": eq(A, B, rot=True),
        "shift": dx != 0 and eq(A, shifted(B, dx)),
    }
    for k, v in single.items():
        if v:
            return k
    full_a = no_repeated([no_implied(c) for c in A])
    full_b = no_repeated([no_implied(c) for c in shifted(B, dx)])
    return "several" if eq(full_a, full_b, rot=True) else "other"


rel, built = TTFont(sys.argv[1]), TTFont(sys.argv[2])
counts = collections.Counter()
for name in rel.getGlyphOrder():
    a = rel["glyf"][name]
    p = getattr(a, "program", None)
    if p is None or not p.getBytecode() or a.isComposite() or name not in built["glyf"]:
        continue
    b = built["glyf"][name]
    if b.isComposite():
        counts["other"] += 1
        continue
    k = classify(a, b)
    if k:
        counts[k] += 1
print(" ".join("%s=%d" % kv for kv in sorted(counts.items())))
