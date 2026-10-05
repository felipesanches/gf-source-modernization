#!/usr/bin/env python3
"""Question answered: does this build hold the SAME DIGITISED POINTS as the shipped
binary, or merely the same shapes?

That distinction is what identifies a master. A source re-fitted from cubic curves
renders identically and passes a rendering gate, but its points are new: cu2qu chooses
its own control points, so straight segments survive untouched and every curve is
redrawn. A source the release was actually cut from holds the same coordinates.

So the measure is exact point identity on the raw glyf outlines, with composites
decomposed and their transforms applied, comparing contours up to cyclic rotation and
reversal, at zero tolerance. Implied on-curve midpoints are expanded on both sides so
that a font that stores them and one that omits them compare equal.

This replaces a pen-stream comparison that was measuring bookkeeping rather than shape.
DecomposingRecordingPen re-emits a contour's start point as the closing segment's
endpoint, and canonicalising with that duplicate still in place shifted two point lists
by one relative to each other whenever the fonts began a contour at different indices --
so every coordinate was compared against its neighbour. It scored squadaone's .sfd arm
at 55.79% when 189 of its 190 glyphs are literally the same points, and italiana's at
49.29% when the true figure is 99.5%.

Usage: outline_match.py <shipped.ttf> <built.ttf>
"""
import json
import sys

from fontTools.ttLib import TTFont


def contours_of(font, name):
    """-> list of contours, each a tuple of (x, y, on_curve) with composites resolved."""
    glyf = font["glyf"]
    if name not in glyf.glyphOrder and name not in glyf.glyphs:
        return None
    g = glyf[name]
    try:
        coords, end_pts, flags = g.getCoordinates(glyf)
    except Exception:
        return None
    out, start = [], 0
    for e in end_pts:
        pts = [(int(round(coords[i][0])), int(round(coords[i][1])), flags[i] & 1)
               for i in range(start, e + 1)]
        if pts:
            out.append(expand_implied(pts))
        start = e + 1
    return out


def expand_implied(pts):
    """TrueType lets an on-curve point between two off-curve points be omitted and
    implied at their midpoint. One font may store it and another omit it for the same
    curve, so insert it on both sides before comparing."""
    n = len(pts)
    out = []
    for i, p in enumerate(pts):
        out.append(p)
        q = pts[(i + 1) % n]
        if p[2] == 0 and q[2] == 0:
            out.append(((p[0] + q[0]) // 2, (p[1] + q[1]) // 2, 1))
    return tuple(out)


def drop_degenerate(contour):
    """Remove an off-curve point that sits on top of an adjacent on-curve point.

    A quadratic whose control point coincides with one of its endpoints is the straight
    line between them, which is exactly what the segment becomes once the control point
    is gone. One font may record such a point and another omit it -- BenchNine's
    released `uni0394` has `(403, 1192)` twice, once on-curve and once off -- and the
    two outlines still render identically.

    Not used by main(): the provenance report compares stored points as stored. It is
    here so that a caller asking "does this render the same" has one implementation.
    """
    n = len(contour)
    keep = []
    for i, p in enumerate(contour):
        if p[2] == 0:
            prv = contour[(i - 1) % n]
            nxt = contour[(i + 1) % n]
            if ((prv[2] == 1 and prv[0] == p[0] and prv[1] == p[1])
                    or (nxt[2] == 1 and nxt[0] == p[0] and nxt[1] == p[1])):
                continue
        keep.append(p)
    return tuple(keep)


def canonical(contour):
    """Least rotation over the contour and its reversal: the same ring of points read
    from a different start, or wound the other way, is the same contour."""
    n = len(contour)
    best = None
    for seq in (contour, tuple(reversed(contour))):
        for i in range(n):
            r = seq[i:] + seq[:i]
            if best is None or r < best:
                best = r
    return best


def main():
    a, b = TTFont(sys.argv[1]), TTFont(sys.argv[2])
    if "glyf" not in a or "glyf" not in b:
        print(json.dumps({"error": "not a TrueType outline font"}))
        return
    upm_a, upm_b = a["head"].unitsPerEm, b["head"].unitsPerEm
    ca, cb = a.getBestCmap(), b.getBestCmap()
    common = sorted(set(ca) & set(cb))
    hma, hmb = a["hmtx"].metrics, b["hmtx"].metrics

    identical = same_points = differing = unreadable = adv_identical = 0
    no_curves_identical = curves_identical = curves_total = 0
    examples = []
    for cp in common:
        na, nb = ca[cp], cb[cp]
        if hma.get(na, (None,))[0] == hmb.get(nb, (None,))[0]:
            adv_identical += 1
        pa, pb = contours_of(a, na), contours_of(b, nb)
        if pa is None or pb is None:
            unreadable += 1
            continue
        ka = sorted(canonical(c) for c in pa)
        kb = sorted(canonical(c) for c in pb)
        has_curve = any(p[2] == 0 for c in pa for p in c)
        if has_curve:
            curves_total += 1
        if ka == kb:
            identical += 1
            if has_curve:
                curves_identical += 1
            else:
                no_curves_identical += 1
            continue
        sa = {(p[0], p[1]) for c in pa for p in c}
        sb = {(p[0], p[1]) for c in pb for p in c}
        if sa == sb:
            same_points += 1
        else:
            differing += 1
            if len(examples) < 8:
                examples.append("U+%04X" % cp)

    n = len(common)
    straight_total = n - curves_total - unreadable
    out = {
        "upm_shipped": upm_a, "upm_built": upm_b,
        "cmap_shipped": len(ca), "cmap_built": len(cb), "cmap_common": n,
        "cmap_missing": len(set(ca) - set(cb)), "cmap_extra": len(set(cb) - set(ca)),
        "identical": identical, "same_points": same_points, "differing": differing,
        "unreadable": unreadable, "adv_identical": adv_identical,
        # The refit signature: cu2qu leaves straight segments alone and redraws every
        # curve, so a re-fitted source shows near-total agreement on curveless glyphs
        # and near-total disagreement on curved ones. A master shows neither split.
        "curved_glyphs": curves_total, "curved_identical": curves_identical,
        "straight_glyphs": straight_total, "straight_identical": no_curves_identical,
        "point_identity": round(100.0 * identical / n, 2) if n else 0.0,
        "differing_examples": examples,
    }
    print(json.dumps(out))


if __name__ == "__main__":
    main()
