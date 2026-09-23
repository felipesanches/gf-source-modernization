#!/usr/bin/env python3
"""Question answered: are the released OS/2 sxHeight and sCapHeight exactly what
FontForge's own TTF exporter computes from the unmodified .sfd?

If they are, the two values are a CONVERSION concern -- a converter replicating
FontForge's exporter produces them from the source alone -- and no family needs a
source edit, and no value has to be copied out of a binary.

This is a line-for-line port of FontForge's rule (fontforge/fontforge master,
fontforge/splinefont.c SFStandardHeight/SFXHeight/SFCapHeight and
SPLMaxHeight/SCMaxHeight; fontforge/tottf.c:3498-3510, which calls them with
return_error=true when the source states no OS2XHeight/OS2CapHeight):

  1. For every codepoint in a fixed list -- A-Z plus Greek and Cyrillic capitals
     for the cap height; a c e g m n o p q r s u v w x y z plus Greek and Cyrillic
     lowercase for the x-height -- take the glyph's top and classify it as FLAT (a
     horizontal line segment), ROUND (a curve) or POINTY (a sloped line).
     References count, transformed; a flat top wins a tie.
  2. If there are flat tops: the mode of their heights, averaging a tie for the
     mode. Otherwise the MEAN of the DISTINCT round/pointy heights.
  3. Snap to the nearest BlueValues zone bottom within (ascent+descent)/100.
  4. Truncate toward zero into a short; a font with none of the glyphs gets 0.

An earlier probe, sfd-batch7/tools/probe_os2_heights_from_source.py, measured
only the yMax of 'x' and 'H', matched 7 of 30 styles, and concluded the heights
"cannot come from the source". That conclusion was wrong: it tested a different
rule from the one FontForge uses.

Usage: gftools/venv/bin/python3 tools/ff_heights_oracle.py [families.tsv]
Exit 1 if any style whose release carries the fields disagrees.
"""
import math
import subprocess
import sys

from fontTools.ttLib import TTFont

ARC = "/home/fsanches/compartilhado/upstream_repos/repo_archive"
RANGE = None  # marker in the lists below

CAP = [ord('A'), RANGE, ord('Z'), 0x391, RANGE, 0x3A9,
       0x402, 0x404, 0x405, 0x406, 0x408, RANGE, 0x40B, 0x40F, RANGE, 0x418,
       0x41A, 0x42F]
XH = [ord(c) for c in "acegmnopqrsuvwxyz"] + [0x131,
      0x3B3, 0x3B9, 0x3BA, 0x3BC, 0x3BD, 0x3C0, 0x3C3, 0x3C4, 0x3C5, 0x3C7, 0x3C8, 0x3C9,
      0x432, 0x433, 0x438, 0x43A, RANGE, 0x43F, 0x442, 0x443, 0x445, 0x44C, 0x44F,
      0x459, 0x45A]

FLAT, ROUND, POINTY, UNKNOWN = "flat", "round", "pointy", "unknown"


def expand(lst):
    """FontForge's walk: `x RANGE y` means x..y inclusive."""
    out, i = [], 0
    while i < len(lst):
        lo = hi = lst[i]
        if i + 2 < len(lst) and lst[i + 1] is RANGE:
            hi = lst[i + 2]
            i += 2
        out.extend(range(lo, hi + 1))
        i += 1
    return out


class Sfd:
    def __init__(self, text):
        self.ascent = self.descent = 0
        self.order2 = False
        self.blues = None
        self.glyphs = {}      # gid -> {"contours": [...], "refs": [...]}
        self.by_uni = {}      # unicode -> gid
        self._parse(text)

    def _parse(self, text):
        lines = text.split("\n")
        i, n = 0, len(lines)
        in_private = False
        cur = None
        layer_fore = False
        in_spl = False
        contour = None
        while i < n:
            ln = lines[i]
            s = ln.strip()
            if cur is None:
                if s.startswith("Ascent:"):
                    self.ascent = float(s.split()[1])
                elif s.startswith("Descent:"):
                    self.descent = float(s.split()[1])
                elif s.startswith("Order2:"):
                    self.order2 = s.split()[1] == "1"
                elif s.startswith("Layer: 1 "):
                    self.order2 = s.split()[2] == "1"
                elif s.startswith("BeginPrivate:"):
                    in_private = True
                elif s.startswith("EndPrivate"):
                    in_private = False
                elif in_private and s.startswith("BlueValues "):
                    body = s.split(" ", 2)[2]
                    self.blues = body
                elif s.startswith("StartChar:"):
                    cur = {"contours": [], "refs": [], "gid": None, "uni": None}
                    layer_fore = True   # glyph data before any layer marker is Fore
                    in_spl = False
            else:
                if s.startswith("Encoding:"):
                    p = s.split()
                    cur["uni"], cur["gid"] = int(p[2]), int(p[3])
                elif s == "Fore":
                    layer_fore = True
                elif s == "Back":
                    layer_fore = False
                elif s.startswith("Layer:"):
                    layer_fore = s.split()[1] == "1"
                elif s == "SplineSet":
                    in_spl = True
                    contour = None
                elif s == "EndSplineSet":
                    in_spl = False
                elif in_spl and layer_fore and s:
                    self._point(cur, s)
                elif s.startswith("Refer:") and layer_fore:
                    p = s.split()
                    # Refer: gid unicode S|N a b c d e f ...
                    cur["refs"].append((int(p[1]), [float(v) for v in p[4:10]]))
                elif s.startswith("EndChar"):
                    if cur["gid"] is not None:
                        self.glyphs[cur["gid"]] = cur
                        if cur["uni"] is not None and cur["uni"] >= 0:
                            self.by_uni.setdefault(cur["uni"], cur["gid"])
                    cur = None
            i += 1

    def _point(self, g, s):
        tok = s.split()
        # the operator is the token that is exactly m, l or c
        op_i = next((k for k, t in enumerate(tok) if t in ("m", "l", "c")), None)
        if op_i is None:
            return
        op = tok[op_i]
        nums = [float(t) for t in tok[:op_i]]
        if op == "m":
            g["contours"].append([("m", (nums[0], nums[1]))])
        elif op == "l":
            g["contours"][-1].append(("l", (nums[0], nums[1])))
        else:
            g["contours"][-1].append(("c", (nums[0], nums[1]), (nums[2], nums[3]),
                                      (nums[4], nums[5])))


def seg_list(contours, xf=None):
    """Yield (p0, cp1, cp2, p3, linear) in FontForge's order, transformed."""
    def T(p):
        if xf is None:
            return p
        a, b, c, d, e, f = xf
        return (a * p[0] + c * p[1] + e, b * p[0] + d * p[1] + f)
    for con in contours:
        prev = None
        for item in con:
            if item[0] == "m":
                prev = T(item[1])
            elif item[0] == "l":
                p = T(item[1])
                yield (prev, prev, p, p, True)
                prev = p
            else:
                c1, c2, p = T(item[1]), T(item[2]), T(item[3])
                linear = (c1 == prev and c2 == p)
                yield (prev, c1, c2, p, linear)
                prev = p


def curve_extrema_y(p0, c1, c2, p3, order2):
    ys = []
    if order2:
        # the single quadratic control point is written twice
        y0, q, y2 = p0[1], c1[1], p3[1]
        den = y0 - 2 * q + y2
        if den != 0:
            t = (y0 - q) / den
            if 0 < t < 1:
                ys.append((1 - t) ** 2 * y0 + 2 * (1 - t) * t * q + t * t * y2)
        return ys
    y0, y1, y2, y3 = p0[1], c1[1], c2[1], p3[1]
    a = -y0 + 3 * y1 - 3 * y2 + y3
    b = 3 * y0 - 6 * y1 + 3 * y2
    c = -3 * y0 + 3 * y1
    # dy/dt = 3a t^2 + 2b t + c
    A, B, C = 3 * a, 2 * b, c
    roots = []
    if abs(A) < 1e-12:
        if abs(B) > 1e-12:
            roots.append(-C / B)
    else:
        disc = B * B - 4 * A * C
        if disc >= 0:
            r = math.sqrt(disc)
            roots += [(-B + r) / (2 * A), (-B - r) / (2 * A)]
    for t in roots:
        if 0 < t < 1:
            ys.append(((a * t + b) * t + c) * t + y0)
    return ys


def spl_max(contours, order2, xf=None):
    """SPLMaxHeight: the top of a set of contours and how it is shaped."""
    f, mx = UNKNOWN, -1e23
    for p0, c1, c2, p3, linear in seg_list(contours, xf):
        if not (p0[1] >= mx or p3[1] >= mx or c1[1] > mx or c2[1] > mx):
            continue
        if not linear:
            if p0[1] > mx:
                f, mx = ROUND, p0[1]
            if p3[1] > mx:
                f, mx = ROUND, p3[1]
            for y in curve_extrema_y(p0, c1, c2, p3, order2):
                if y > mx:
                    f, mx = ROUND, y
        elif p0[1] == p3[1]:
            if p0[1] >= mx:
                f, mx = FLAT, p0[1]
        else:
            if p0[1] > mx:
                f, mx = POINTY, p0[1]
            if p3[1] > mx:
                f, mx = POINTY, p3[1]
    return mx, f


def flat_contours(sfd, gid, xf, depth=0):
    """A reference's r->layers[0].splines: the referenced glyph's own contours plus,
    flattened in, those of its own references -- all transformed. FontForge keeps
    this one list per reference and measures it with a single SPLMaxHeight."""
    g = sfd.glyphs[gid]
    out = [[(it[0],) + tuple(apply(xf, p) for p in it[1:]) for it in con] for con in g["contours"]]
    if depth < 8:
        for rgid, rxf in g["refs"]:
            if rgid in sfd.glyphs:
                out += flat_contours(sfd, rgid, compose(rxf, xf), depth + 1)
    return out


def apply(xf, p):
    if xf is None:
        return p
    a, b, c, d, e, f = xf
    return (a * p[0] + c * p[1] + e, b * p[0] + d * p[1] + f)


def sc_max(sfd, gid):
    """SCMaxHeight: own contours, then each reference's flattened contours; a
    reference replaces the running top when higher, or equal and flat."""
    g = sfd.glyphs[gid]
    mx, f = spl_max(g["contours"], sfd.order2)
    for rgid, rxf in g["refs"]:
        if rgid not in sfd.glyphs:
            continue
        t, cf = spl_max(flat_contours(sfd, rgid, rxf), sfd.order2)
        if t > mx or (t == mx and cf == FLAT):
            mx, f = t, cf
    return mx, f


def compose(inner, outer):
    if outer is None:
        return inner
    a, b, c, d, e, f = inner
    A, B, C, D, E, F = outer
    return (a * A + b * C, a * B + b * D, c * A + d * C, c * B + d * D,
            e * A + f * C + E, e * B + f * D + F)


def standard_height(sfd, lst):
    flats, curves = [], []          # [pos, cnt]
    for ch in expand(lst):
        gid = sfd.by_uni.get(ch)
        if gid is None:
            continue
        t, f = sc_max(sfd, gid)
        bucket = flats if f == FLAT else (curves if f != UNKNOWN else None)
        if bucket is None:
            continue
        for e in bucket:
            if e[0] == t:
                e[1] += 1
                break
        else:
            bucket.append([t, 1])
    if len(flats) == 1:
        result = flats[0][0]
    elif flats:
        top = max(c for _, c in flats)
        tied = [p for p, c in flats if c == top]
        result = sum(tied) / len(tied)
    elif not curves:
        return None                  # no glyphs: the exporter writes 0
    else:
        result = sum(p for p, _ in curves) / len(curves)
    if sfd.blues:
        vals = []
        for tok in sfd.blues.replace("[", " ").replace("]", " ").split():
            try:
                vals.append(float(tok))
            except ValueError:
                break
        best, bestdiff = result, (sfd.ascent + sfd.descent) / 100.0
        for v in vals[0::2]:
            if abs(v - result) < bestdiff:
                best, bestdiff = v, abs(v - result)
        result = best
    return result


def exported(v):
    """os2->xHeight = (xh >= 0.0 ? xh : 0) into a short: truncation."""
    return 0 if v is None or v < 0 else int(v)


def main():
    fam_tsv = sys.argv[1] if len(sys.argv) > 1 else "families.tsv"
    rows = [l.rstrip("\n").split("\t") for l in open(fam_tsv)][1:]
    bad = checked = 0
    print("%-26s %-5s %-13s %-13s %s" % ("style", "rOS2", "x ff/rel", "cap ff/rel", "verdict"))
    for repo, fam, lic, kind, base, commit, style, src, shipped in rows:
        path = f"{lic}/{fam}/{src}" if kind == "hg" else src
        text = subprocess.run(["git", "-C", f"{ARC}/{base}.git", "show", f"{commit}:{path}"],
                              capture_output=True, check=True).stdout.decode("utf-8", "replace")
        sfd = Sfd(text)
        hdr = {k: v for k, v in (l.split(":", 1) for l in text.split("\nStartChar:", 1)[0].split("\n") if ":" in l)}
        stated_x = float(hdr["OS2XHeight"]) if "OS2XHeight" in hdr else 0
        stated_c = float(hdr["OS2CapHeight"]) if "OS2CapHeight" in hdr else 0
        x = int(stated_x) if stated_x else exported(standard_height(sfd, XH))
        c = int(stated_c) if stated_c else exported(standard_height(sfd, CAP))
        o2 = TTFont(shipped)["OS/2"]
        if o2.version < 2:
            print("%-26s v%-4d %-13s %-13s release carries no heights" % (style, o2.version, x, c))
            continue
        checked += 1
        ok = (x, c) == (o2.sxHeight, o2.sCapHeight)
        bad += not ok
        print("%-26s v%-4d %-13s %-13s %s%s" % (style, o2.version, "%s/%s" % (x, o2.sxHeight),
              "%s/%s" % (c, o2.sCapHeight), "MATCH" if ok else "DIFFER",
              "  (stated in .sfd)" if (stated_x or stated_c) else ""))
    print()
    print("FontForge's rule reproduces the release: %d of %d styles that carry the fields"
          % (checked - bad, checked))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
