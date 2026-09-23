#!/usr/bin/env python3
"""Question answered: what OS/2 sxHeight/sCapHeight did FontForge's TTF exporter
write for a given .sfd, AT A GIVEN FONTFORGE VINTAGE -- and which glyph tops
produced it?

An independent re-implementation (it does not import tools/ff_heights_oracle.py),
written from the FontForge C at two commits:

  2011  b69c9652760b (2011-02-22, the FontForge the FFTM "20110222" builds carry):
        splinefont.c SFStandardHeight: curve mean = sum of DISTINCT heights divided
        by the number of GLYPHS (`tot += curves[i].cnt`); splineutil2.c
        SplineIsLinear calls MinMaxWithin for a vertical/horizontal chord even when
        the control points are off the chord (no `ret &&`); RealNear is relative
        (|a-b| < |a|/2^20).
  2012  5a11aa4c0ab4 (2012-09-06, the FFTM build of PatrickHand) == master for this
        path: curve mean over DISTINCT heights (`++tot`, fontforge 4d34d21ef866,
        2012-05-14); `ret &&` present; RealNear absolute (1e-6).

Both vintages: SFGetChar -> SFFindGID: the LOWEST gid whose unicode OR AltUni
matches; SCMaxHeight: own contours, then each reference's flattened, transformed
contours (a reference wins when higher, or equal and flat); SPLMaxHeight exactly as
in C, including MinMaxWithin evaluating its second root even when it is -1;
BlueValues snap to the nearest zone bottom within (ascent+descent)/100; the double
is truncated into the int16 field. Order-2 splines: SplineRefigure2 (c = 2(cp-p0),
b = p3-p0-c, a = 0); a control point equal to its end point makes the spline a line.

Usage:
  <venv python3> ff_heights_probe.py all [families.tsv]      every style, both vintages
  <venv python3> ff_heights_probe.py dump <file.sfd> [2011|2012]   per-glyph tops
"""
import math
import subprocess
import sys

ARC = "/home/fsanches/compartilhado/upstream_repos/repo_archive"
FAM = "/home/fsanches/compartilhado/sfd-reland/families.tsv"

R = None
CAP = [0x41, R, 0x5A, 0x391, R, 0x3A9, 0x402, 0x404, 0x405, 0x406, 0x408, R, 0x40B,
       0x40F, R, 0x418, 0x41A, 0x42F]
XH = [ord(c) for c in "acegmnopqrsuvwxyz"] + [0x131, 0x3B3, 0x3B9, 0x3BA, 0x3BC, 0x3BD,
      0x3C0, 0x3C3, 0x3C4, 0x3C5, 0x3C7, 0x3C8, 0x3C9, 0x432, 0x433, 0x438, 0x43A, R,
      0x43F, 0x442, 0x443, 0x445, 0x44C, 0x44F, 0x459, 0x45A]


def walk(lst):
    i = 0
    while i < len(lst):
        lo = hi = lst[i]
        if i + 2 < len(lst) and lst[i + 1] is R:
            hi = lst[i + 2]
            i += 2
        yield from range(lo, hi + 1)
        i += 1


# ---------------------------------------------------------------- SFD parsing
def parse(text):
    font = {"ascent": 0.0, "descent": 0.0, "order2": False, "blues": None, "glyphs": {}}
    g = None
    fore = True
    inspl = False
    inpriv = False
    for raw in text.split("\n"):
        s = raw.strip()
        if g is None:
            if s.startswith("Ascent:"):
                font["ascent"] = float(s.split()[1])
            elif s.startswith("Descent:"):
                font["descent"] = float(s.split()[1])
            elif s.startswith("Order2:"):
                font["order2"] = s.split()[1] == "1"
            elif s.startswith("Layer: 1 "):
                font["order2"] = s.split()[2] == "1"
            elif s.startswith("BeginPrivate:"):
                inpriv = True
            elif s.startswith("EndPrivate"):
                inpriv = False
            elif inpriv and s.startswith("BlueValues "):
                font["blues"] = s.split(" ", 2)[2]
            elif s.startswith("StartChar:"):
                g = {"name": s.split(":", 1)[1].strip(), "unis": [], "gid": None,
                     "contours": [], "refs": []}
                fore, inspl = True, False
            continue
        if s.startswith("Encoding:"):
            p = s.split()
            g["gid"] = int(p[3])
            if int(p[2]) >= 0:
                g["unis"].append(int(p[2]))
        elif s.startswith("AltUni2:"):
            for item in s.split()[1:]:
                u = int(item.split(".")[0], 16)
                g["unis"].append(u)
        elif s == "Fore":
            fore = True
        elif s == "Back":
            fore = False
        elif s.startswith("Layer:"):
            fore = s.split()[1] == "1"
        elif s == "SplineSet":
            inspl = True
        elif s == "EndSplineSet":
            inspl = False
        elif s.startswith("Refer:") and fore:
            p = s.split()
            g["refs"].append((int(p[1]), tuple(float(v) for v in p[4:10])))
        elif s == "EndChar":
            font["glyphs"][g["gid"]] = g
            g = None
        elif inspl and fore and s:
            tok = s.split()
            k = next((i for i, t in enumerate(tok) if t in ("m", "l", "c")), None)
            if k is None:
                continue
            v = [float(t) for t in tok[:k]]
            if tok[k] == "m":
                g["contours"].append([("m", (v[-2], v[-1]))])
            elif tok[k] == "l":
                g["contours"][-1].append(("l", (v[-2], v[-1])))
            else:
                g["contours"][-1].append(("c", (v[-6], v[-5]), (v[-4], v[-3]), (v[-2], v[-1])))
    return font


def xform(p, m):
    a, b, c, d, e, f = m
    return (a * p[0] + c * p[1] + e, b * p[0] + d * p[1] + f)


def mul(inner, outer):
    a, b, c, d, e, f = inner
    A, B, C, D, E, F = outer
    return (a * A + b * C, a * B + b * D, c * A + d * C, c * B + d * D,
            e * A + f * C + E, e * B + f * D + F)


def segments(contours, m=None):
    """Splines of each contour as (p0, nextcp, prevcp, p3), in FontForge's order.
    SFDCloseCheck re-makes the last spline to end exactly on the first point."""
    T = (lambda p: p) if m is None else (lambda p: xform(p, m))
    out = []
    for con in contours:
        segs = []
        prev = T(con[0][1])
        first = prev
        for it in con[1:]:
            if it[0] == "l":
                p = T(it[1])
                segs.append([prev, prev, p, p])
            else:
                p = T(it[3])
                segs.append([prev, T(it[1]), T(it[2]), p])
            prev = p
        out.append(segs)
    return out


# ---------------------------------------------------------- FontForge numerics
class V:
    """One vintage's numeric helpers."""

    def __init__(self, year):
        self.year = year

    def near(self, a, b):
        if a == 0:
            return -1e-8 < b < 1e-8
        if b == 0:
            return -1e-8 < a < 1e-8
        if self.year == 2011:       # d = a/(1024*1024.) ; |a-b| < |d|
            d = abs(a / (1024 * 1024.0))
            return -d < a - b < d
        return -1e-6 < a - b < 1e-6

    @staticmethod
    def approx(a, b):
        if a == 0:
            return -.0001 < b < .0001
        if b == 0:
            return -.0001 < a < .0001
        r = a / b
        return .95 <= r <= 1.05

    @staticmethod
    def within16(v1, v2):
        nz, fac = .00000001, 1024.0 ** 5 * 2.0
        t = v1 * v2
        if t < 0:
            return False
        if t == 0:
            v = v2 if v1 == 0 else v1
            return -nz < v < nz
        if v1 > 0:
            return (v1 - v2 < v1 / (fac / 16)) if v1 > v2 else (v2 - v1 < v2 / (fac / 16))
        return (v1 - v2 > v1 / (fac / 16)) if v1 < v2 else (v2 - v1 > v2 / (fac / 16))

    def extrema(self, a, b, c):
        t1 = t2 = -1.0
        if a != 0:
            disc = 4 * b * b - 12 * a * c
            if disc >= 0:
                r = math.sqrt(disc)
                t1 = (-2 * b - r) / (6 * a)
                t2 = (-2 * b + r) / (6 * a)
                if t1 > t2:
                    t1, t2 = t2, t1
                elif t1 == t2:
                    t2 = -1.0
                if self.near(t1, 0): t1 = 0.0
                elif self.near(t1, 1): t1 = 1.0
                if self.near(t2, 0): t2 = 0.0
                elif self.near(t2, 1): t2 = 1.0
                if t2 <= 0 or t2 >= 1: t2 = -1.0
                if t1 <= 0 or t1 >= 1: t1, t2 = t2, -1.0
        elif b != 0:
            t1 = -c / (2.0 * b)
            if t1 <= 0 or t1 >= 1:
                t1 = -1.0
        return t1, t2


class Spl:
    def __init__(self, v, seg, order2):
        p0, n, pv, p3 = seg
        self.v = v
        if order2 and n != pv and not (n == p0 or pv == p3):
            mid = ((n[0] + pv[0]) / 2, (n[1] + pv[1]) / 2)   # SplineRefigure2 averages
            n = pv = mid
        self.p0, self.n, self.pv, self.p3 = p0, n, pv, p3
        line = (n == p0 or pv == p3) if order2 else (n == p0 and pv == p3)
        if line:
            n = pv = None
        self.co = []
        for k in (0, 1):
            if line:
                self.co.append([0.0, 0.0, p3[k] - p0[k], p0[k]])
                continue
            if order2:
                c = 2 * (self.n[k] - p0[k]); b = p3[k] - p0[k] - c; a = 0.0
            else:
                c = 3 * (self.n[k] - p0[k]); b = 3 * (self.pv[k] - self.n[k]) - c
                a = p3[k] - p0[k] - c - b
            if v.near(c, 0): c = 0.0
            if v.near(b, 0): b = 0.0
            if v.near(a, 0): a = 0.0
            self.co.append([a, b, c, p0[k]])
        if line:
            self.n, self.pv = p0, p3
        self.linear = line or (self.co[0][:2] == [0, 0] and self.co[1][:2] == [0, 0])
        if not self.linear:
            self.linear = self.is_linear()

    def minmax_within(self):
        p0, p3 = self.p0, self.p3
        w_ = 1 if abs(p3[0] - p0[0]) < abs(p3[1] - p0[1]) else 0
        a, b, c, d = self.co[w_]
        t1, t2 = self.v.extrema(a, b, c)
        if t1 == -1:
            return True
        for t in (t1, t2):                    # C evaluates t2 even when it is -1
            w = ((a * t + b) * t + c) * t + d
            if self.v.near(w, p3[w_]) or self.v.near(w, p0[w_]):
                continue
            if (w < p3[w_] and w < p0[w_]) or (w > p3[w_] and w > p0[w_]):
                return False
        return True

    def is_linear(self):
        v, p0, n, pv, p3 = self.v, self.p0, self.n, self.pv, self.p3
        strict = v.year != 2011
        if v.near(p0[0], p3[0]):
            ret = v.near(p0[0], n[0]) and v.near(p0[0], pv[0])
            inr = ((n[1] >= p0[1] and n[1] <= p3[1] and pv[1] >= p0[1] and pv[1] <= p3[1]) or
                   (n[1] <= p0[1] and n[1] >= p3[1] and pv[1] <= p0[1] and pv[1] >= p3[1]))
            if (ret or not strict) and not inr:
                ret = self.minmax_within()
        elif v.near(p0[1], p3[1]):
            ret = v.near(p0[1], n[1]) and v.near(p0[1], pv[1])
            inr = ((n[0] >= p0[0] and n[0] <= p3[0] and pv[0] >= p0[0] and pv[0] <= p3[0]) or
                   (n[0] <= p0[0] and n[0] >= p3[0] and pv[0] <= p0[0] and pv[0] >= p3[0]))
            if (ret or not strict) and not inr:
                ret = self.minmax_within()
        else:
            t1 = (n[1] - p0[1]) / (p3[1] - p0[1]); t2 = (n[0] - p0[0]) / (p3[0] - p0[0])
            t3 = (p3[1] - pv[1]) / (p3[1] - p0[1]); t4 = (p3[0] - pv[0]) / (p3[0] - p0[0])
            ret = ((v.within16(t1, t2) or (v.approx(t1, 0) and v.approx(t2, 0))) and
                   (v.within16(t3, t4) or (v.approx(t3, 0) and v.approx(t4, 0))))
            if ret and any(t < 0 or t > 1 for t in (t1, t2, t3, t4)):
                ret = self.minmax_within()
        if ret:
            self.co = [[0.0, 0.0, p3[0] - p0[0], p0[0]], [0.0, 0.0, p3[1] - p0[1], p0[1]]]
        return ret


def spl_max(v, contours, order2):
    f, mx = "unknown", -1e23
    for con in contours:
        for seg in con:
            p0, n, pv, p3 = seg
            if not (p0[1] >= mx or p3[1] >= mx or n[1] > mx or pv[1] > mx):
                continue
            s = Spl(v, seg, order2)
            if not s.linear:
                if p0[1] > mx: f, mx = "round", p0[1]
                if p3[1] > mx: f, mx = "round", p3[1]
                a, b, c, d = s.co[1]
                for t in v.extrema(a, b, c):
                    if t != -1:
                        y = ((a * t + b) * t + c) * t + d
                        if y > mx: f, mx = "round", y
            elif p0[1] == p3[1]:
                if p0[1] >= mx: f, mx = "flat", p0[1]
            else:
                if p0[1] > mx: f, mx = "pointy", p0[1]
                if p3[1] > mx: f, mx = "pointy", p3[1]
    return mx, f


def ref_contours(font, gid, m, depth=0):
    """RefChar.layers[0].splines: the referenced glyph's own contours, then its
    references' (SCReinstanciateRefChar), all transformed."""
    g = font["glyphs"][gid]
    out = segments(g["contours"], m)
    if depth < 16:
        for rg, rm in g["refs"]:
            if rg in font["glyphs"]:
                out += ref_contours(font, rg, mul(rm, m), depth + 1)
    return out


def sc_max(v, font, g):
    mx, f = spl_max(v, segments(g["contours"]), font["order2"])
    for rg, rm in g["refs"]:
        if rg not in font["glyphs"]:
            continue
        t, cf = spl_max(v, ref_contours(font, rg, rm), font["order2"])
        if t > mx or (t == mx and cf == "flat"):
            mx, f = t, cf
    return mx, f


def find(font, u):
    for gid in sorted(font["glyphs"]):
        if u in font["glyphs"][gid]["unis"]:
            return font["glyphs"][gid]
    return None


def standard_height(v, font, lst, trace=None):
    flats, curves = [], []
    for ch in walk(lst):
        g = find(font, ch)
        if g is None:
            continue
        t, f = sc_max(v, font, g)
        if trace is not None:
            trace.append((ch, g["name"], t, f))
        if f == "unknown":
            continue
        b = flats if f == "flat" else curves
        for e in b:
            if e[0] == t:
                e[1] += 1
                break
        else:
            b.append([t, 1])
    if len(flats) == 1:
        res = flats[0][0]
    elif flats:
        top = max(c for _, c in flats)
        tied = [p for p, c in flats if c == top]
        res = sum(tied) / len(tied)
    elif not curves:
        return None, flats, curves
    else:
        den = sum(c for _, c in curves) if v.year == 2011 else len(curves)
        res = sum(p for p, _ in curves) / den
    raw = res
    if font["blues"]:
        body = font["blues"].lstrip(" [")
        vals = []
        for tok in body.replace("]", " ] ").split():
            if tok == "]":
                break
            try:
                vals.append(float(tok))
            except ValueError:
                break
        best, bd = res, (font["ascent"] + font["descent"]) / 100.0
        for x in vals[0::2]:
            if abs(x - res) < bd:
                best, bd = x, abs(x - res)
        res = best
    return (raw, res), flats, curves


def exported(r):
    if r is None:
        return 0
    v = r[1]
    return int(v) if v >= 0 else 0      # (xh >= 0.0 ? xh : 0) into an int16


def heights(text, year):
    v = V(year)
    font = parse(text)
    x = standard_height(v, font, XH)[0]
    c = standard_height(v, font, CAP)[0]
    return exported(x), exported(c), x, c


def cmd_all(tsv):
    from fontTools.ttLib import TTFont
    import datetime
    E = datetime.datetime(1904, 1, 1, tzinfo=datetime.timezone.utc)
    rows = [l.rstrip("\n").split("\t") for l in open(tsv)][1:]
    print("%-27s %-10s %-9s %-9s %-9s %-9s %-9s %s" % (
        "style", "FFTM", "x2011", "x2012", "xrel", "c2011", "c2012", "crel  verdict"))
    for repo, fam, lic, kind, base, commit, style, src, shipped in rows:
        path = "%s/%s/%s" % (lic, fam, src) if kind == "hg" else src
        r = subprocess.run(["git", "-C", "%s/%s.git" % (ARC, base), "show",
                            "%s:%s" % (commit, path)], capture_output=True)
        if r.returncode:
            print("%-27s NO SOURCE" % style)
            continue
        text = r.stdout.decode("utf-8", "replace")
        hdr = text.split("\nStartChar:", 1)[0]
        stated = "OS2XHeight:" in hdr or "OS2CapHeight:" in hdr
        f = TTFont(shipped)
        o = f["OS/2"]
        if o.version < 2:
            continue
        stamp = "-"
        if "FFTM" in f:
            stamp = (E + datetime.timedelta(seconds=f["FFTM"].FFTimeStamp)).strftime("%Y-%m-%d")
        a = heights(text, 2011)
        b = heights(text, 2012)
        rel = (o.sxHeight, o.sCapHeight)
        verdict = []
        if a[:2] == rel: verdict.append("2011")
        if b[:2] == rel: verdict.append("2012")
        print("%-27s %-10s %-9d %-9d %-9d %-9d %-9d %-5d %s%s" % (
            style, stamp, a[0], b[0], rel[0], a[1], b[1], rel[1],
            "+".join(verdict) or "NEITHER", "  (sfd states heights)" if stated else ""))


def cmd_dump(path, year):
    v = V(year)
    font = parse(open(path, encoding="utf-8", errors="replace").read())
    print("order2=%s ascent=%s descent=%s blues=%s vintage=%d" % (
        font["order2"], font["ascent"], font["descent"], font["blues"], year))
    for name, lst in (("x-height", XH), ("cap height", CAP)):
        tr = []
        res, flats, curves = standard_height(v, font, lst, tr)
        print("== %s" % name)
        for ch, gname, t, f in tr:
            print("  U+%04X %-14s %-8s %.6f" % (ch, gname, f, t))
        print("  flats  (height,count): %s" % [(round(p, 6), c) for p, c in flats])
        print("  curves (height,count): %s" % [(round(p, 6), c) for p, c in curves])
        if curves and not flats:
            s = sum(p for p, _ in curves)
            print("  curve sum %.6f; distinct %d -> %.6f; glyphs %d -> %.6f" % (
                s, len(curves), s / len(curves), sum(c for _, c in curves),
                s / sum(c for _, c in curves)))
        print("  raw %s -> after BlueValues %s -> exported %d" % (
            None if res is None else round(res[0], 6), None if res is None else round(res[1], 6),
            exported(res)))


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "dump":
        cmd_dump(sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 2012)
    else:
        cmd_all(sys.argv[2] if len(sys.argv) > 2 else FAM)
