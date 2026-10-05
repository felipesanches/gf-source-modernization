#!/usr/bin/env python3
"""Question answered: for one shipped/built pair that fails the functional gate's
`rendering` (or `advances`) check, WHICH glyphs differ and HOW -- so each failure can be
assigned a root cause.

Reuses tools/functional_gate.py (same Font normalisation, correspondence, FreeType
geometry test and thresholds), and for every reachable glyph that fails the geometry test
(> 4 px at 64/255 fuzz, 1 px = 8 units) or that diffenator3 reports and the gate confirms,
prints a classification:

  STALE-LSB      release glyf points == build points, but release hmtx lsb != glyf xMin,
                 so a TrueType rasterizer draws the release shifted by lsb - xMin.
  RAW-SAME       normalised outlines identical without any lsb shift (should not fail).
  SHIFT dx,dy    every point of the build equals the release's moved by a constant.
  ROUND1         same structure, every point within 1 unit (rounding).
  MOVED n/m max  same structure (same contour/point counts after normalisation), n of m
                 points moved, max displacement d units.
  STRUCT         different contour or point counts (refit, overlap removal, missing or
                 extra contours); prints both counts.
  COMPONENT      composite in one font and simple in the other, or component offsets
                 differ (offsets printed).
  ADV a/b        advances differ.
And for diffenator3 glyph reports: whether the confirmation came from geometry or from
HarfBuzz shaping (a run difference, e.g. mark positioning) -- the latter is not an outline
difference at all.

usage: diagnose.py <shipped.ttf> <built.ttf> <workdir> [--all-changed]
"""
import json
import os
import sys

sys.path.insert(0, "/home/fsanches/compartilhado/gf-source-modernization/tools")
import functional_gate as fg  # noqa: E402
import freetype  # noqa: E402


def raw_outline(F, name):
    """Normalised outline with NO lsb shift (the glyf points as stored)."""
    tt = F.tt
    g = tt["glyf"][name]
    if not g.numberOfContours:
        return ()
    coords, ends, flags = g.getCoordinates(tt["glyf"])
    cs, s = [], 0
    for e in ends:
        pts = [(round(x), round(y), f & 1) for (x, y), f in zip(coords[s:e + 1], flags[s:e + 1])]
        s = e + 1
        cs.append(fg.canonical_contour(pts))
    return tuple(sorted(cs))


def comps(F, name):
    g = F.tt["glyf"][name]
    if g.isComposite():
        return [(c.glyphName, c.x, c.y, tuple(round(v, 5) for v in (getattr(c, "transform", [[1, 0], [0, 1]])[0] + getattr(c, "transform", [[1, 0], [0, 1]])[1])) if hasattr(c, "transform") else None) for c in g.components]
    return None


def struct(sig):
    return tuple(sorted(len(c) for c in sig))


def classify(A, B, na, nb):
    out = []
    ga, gb = A.tt["glyf"][na], B.tt["glyf"][nb]
    ga.recalcBounds(A.tt["glyf"]) if ga.numberOfContours else None
    la, lb = A.tt["hmtx"][na], B.tt["hmtx"][nb]
    xa = getattr(ga, "xMin", 0) if ga.numberOfContours else 0
    xb = getattr(gb, "xMin", 0) if gb.numberOfContours else 0
    if la[0] != lb[0]:
        out.append("ADV %d/%d" % (la[0], lb[0]))
    stale = la[1] - xa
    ra, rb = raw_outline(A, na), raw_outline(B, nb)
    ca, cb = comps(A, na), comps(B, nb)
    if (ca is None) != (cb is None):
        out.append("COMPONENT release=%s build=%s" % (ca, cb))
    elif ca and cb and ca != cb:
        out.append("COMPONENT offsets release=%s build=%s" % (ca, cb))
    if ra == rb:
        out.append("STALE-LSB lsb-xMin=%+d (release lsb %d xMin %d; build lsb %d xMin %d)" % (stale, la[1], xa, lb[1], xb) if stale else "RAW-SAME")
        return out
    if stale:
        out.append("release stale lsb %+d" % stale)
    if not ra or not rb:
        out.append("EMPTY release=%d build=%d contours" % (len(ra), len(rb)))
        return out
    if struct(ra) == struct(rb):
        # pair contours in sorted-by-structure order, compare point by point
        pa = sorted(ra, key=lambda c: (len(c), c))
        pb = sorted(rb, key=lambda c: (len(c), c))
        # try best pairing: for each contour in a, the b contour of same length minimising displacement
        used, moved, total, mx, deltas = set(), 0, 0, 0, set()
        for c in pa:
            best = None
            for j, d in enumerate(pb):
                if j in used or len(d) != len(c):
                    continue
                # allow rotation of start
                for k in range(len(d)):
                    dd = d[k:] + d[:k]
                    m = max(max(abs(p[0] - q[0]), abs(p[1] - q[1])) for p, q in zip(c, dd))
                    if best is None or m < best[0]:
                        best = (m, j, dd)
            if best is None:
                out.append("STRUCT(pairing)")
                return out
            used.add(best[1])
            for p, q in zip(c, best[2]):
                total += 1
                if p[:2] != q[:2]:
                    moved += 1
                    deltas.add((q[0] - p[0], q[1] - p[1]))
            mx = max(mx, best[0])
        if len(deltas) == 1:
            out.append("SHIFT %s (%d/%d pts)" % (next(iter(deltas)), moved, total))
        elif mx <= 1:
            out.append("ROUND1 %d/%d pts" % (moved, total))
        else:
            out.append("MOVED %d/%d pts max %d deltas %s" % (moved, total, mx, sorted(deltas)[:6]))
    else:
        out.append("STRUCT release %d contours %s / build %d contours %s" % (len(ra), struct(ra), len(rb), struct(rb)))
    return out


def main():
    shipped, built, wd = sys.argv[1:4]
    all_changed = "--all-changed" in sys.argv
    os.makedirs(wd, exist_ok=True)
    A, B = fg.Font(shipped), fg.Font(built)
    key_a, key_b, ka, kb = fg.correspondence(A, B)
    inv_b = {k: n for n, k in kb.items()}
    j = os.path.join(wd, os.path.basename(built) + ".fg-d3.json")
    if not os.path.exists(j):
        j = fg.run_d3(shipped, built, wd)
    fa, fb = freetype.Face(A.path), freetype.Face(B.path)
    ppem = max(8, round(A.upem / fg.GEOMETRY_UNITS_PER_PX))
    fa.set_pixel_sizes(0, ppem)
    fb.set_pixel_sizes(0, ppem)
    geo = {}
    changed = []
    for n in sorted(A.reachable()):
        nb = inv_b.get(ka[n])
        if nb is None:
            print("NO-COUNTERPART %s" % n)
            continue
        if A.outline(n) != B.outline(nb):
            px = fg.bitmap_diff(fg.ft_bitmap(fa, A.gid[n]), fg.ft_bitmap(fb, B.gid[nb]), fg.GEOMETRY_FUZZ)
            geo[n] = px
            changed.append(n)
        elif A.tt["hmtx"][n][0] != B.tt["hmtx"][nb][0]:
            print("ADV-ONLY %s %d/%d" % (n, A.tt["hmtx"][n][0], B.tt["hmtx"][nb][0]))
    print("# %s: %d reachable outlines changed, %d fail geometry" % (os.path.basename(shipped), len(changed), sum(1 for n in changed if geo[n] > fg.GEOMETRY_THRESHOLD)))
    for n in sorted(changed, key=lambda n: -geo[n]):
        if geo[n] <= fg.GEOMETRY_THRESHOLD and not all_changed:
            continue
        nb = inv_b[ka[n]]
        tag = "GEO-FAIL" if geo[n] > fg.GEOMETRY_THRESHOLD else "geo-ok"
        print("%s %s(%s) %dpx: %s" % (tag, n, nb, geo[n], "; ".join(classify(A, B, n, nb))))
    # diffenator3 glyph reports: why confirmed?
    d = json.load(open(j))
    SA, SB = fg.Shaper(A, key_a), fg.Shaper(B, key_b)
    for loc in d.get("locations") or []:
        for g in loc.get("glyphs") or []:
            if not isinstance(g, dict):
                continue
            s = g.get("string") or ""
            cp = ord(s[0]) if s else None
            n = A.cmap.get(cp)
            px = geo.get(n, 0) if n else 0
            sh = SA.run(s) != SB.run(s)
            why = []
            if n is None:
                why.append("not in release cmap")
            if px > fg.GEOMETRY_THRESHOLD:
                why.append("geometry %dpx" % px)
            if sh:
                why.append("SHAPING differs: rel=%s build=%s" % (SA.run(s), SB.run(s)))
            print("D3 %s %s %dpx -> %s" % (g.get("unicode"), n, g.get("differing_pixels") or 0, "; ".join(why) or "unconfirmed"))


if __name__ == "__main__":
    main()
