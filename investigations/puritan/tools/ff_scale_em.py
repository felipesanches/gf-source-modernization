#!/usr/bin/env python3
"""Question answered: what does a Puritan .sfd look like after FontForge 20100501
executes `f.em = 1024` on it -- the step src/generate.py ran before exporting the
.ttf files google/fonts ships?

This is a port of exactly the code that statement ran in FontForge 20100501
(fontforge_full-20100501.tar.bz2, libfontforge stamp LibFF_ModTime 1272512607 =
2010-04-29 03:43:27 UTC, which is the FFTM FFTimeStamp every released Puritan
.ttf carries), restricted to what these four sources contain:

  python.c   PyFF_Font_set_em        ds = newem*descent/oldem  (INTEGER division)
                                     as = newem - ds           -> 820 / 204
  splinefont.c SFScaleToEm           scale = (as+ds)/(double)(ascent+descent)
                                     pfminfo fields: rint(v*scale)
                                     upos, uwidth: *= scale (float, not rounded)
  fontviewbase.c FVTrans             width: SCSynchronizeWidth(sc, width*scale)
                                     -> assigned to int16: TRUNCATED
                                     SCTransLayer on every layer; references of
                                     selected glyphs: only the offsets scale
  splineutil.c TransformPoint        p = t*p, then snapped to 1/1024
  splinechar.c SCRound2Int           (active layer = Fore only)
               SplinePointRound      interpolated point (ttfindex 0xffff): round
                                     both controls, me = their midpoint;
                                     otherwise round me and round each control's
                                     OFFSET from me; order2 controls propagate
                                     to the neighbour, first-processed wins
                                     ref offsets: rint

`real` is float in a default 20100501 build, so the arithmetic is emulated in
IEEE single precision. `f.is_quadratic = True` is a no-op (the Fore layers are
already order2) and `f.round()` acts on the selection, which is empty at that
point in generate.py, so neither changes anything.

Usage: ff_scale_em.py <in.sfd> <out.sfd> [--newem 1024] [--int-underline]
  --int-underline  write UnderlinePosition/UnderlineWidth rounded to integers
                   (babelfont f725e6a parses those two fields as i32 and silently
                   drops a real such as -136.192). FontForge's own post export
                   gives the same bytes either way: (short)(upos - uwidth/2).
"""
import math
import struct
import sys


def f32(x):
    return struct.unpack("f", struct.pack("f", x))[0]


def rint(x):
    # C rint() in the default rounding mode: round half to even
    return float(round(x))


def g(x):
    """FontForge writes coordinates with "%g" of (double) real."""
    s = "%g" % x
    return "0" if s == "-0" else s


class Pt:
    __slots__ = ("me", "prevcp", "nextcp", "noprevcp", "nonextcp", "flags",
                 "ttf", "ncp", "interp", "raw_tail", "linear_next")


U16 = {-1: 0xFFFF}


def refigure2(frm, to):
    """splineorder2.c SplineRefigure2, the part that changes points: a spline whose
    control sits on an end point (and whose control has no TrueType number) or whose
    end says it has no control becomes a LINE, both controls reset to the points."""
    if (frm.nonextcp or to.noprevcp
            or (frm.nextcp == frm.me and frm.ncp >= 0xFFFE)
            or (to.prevcp == to.me and frm.ncp >= 0xFFFE)):
        frm.nonextcp = to.noprevcp = True
        frm.nextcp = frm.me
        to.prevcp = to.me
    if frm.nonextcp and to.noprevcp:
        frm.linear_next = True
    else:
        frm.linear_next = False
        if frm.nextcp != to.prevcp:
            m = (f32((frm.nextcp[0] + to.prevcp[0]) / 2), f32((frm.nextcp[1] + to.prevcp[1]) / 2))
            frm.nextcp = to.prevcp = m


def parse_splineset(lines):
    """SFDGetSplineSet for an order2 layer -> list of (points, closed, None)."""
    contours = []
    cur = None
    for ln in lines:
        toks = ln.split()
        kind = toks[-2]
        tail = toks[-1]
        nums = [float(t) for t in toks[:-2]]
        fl = tail.split(",")
        p = Pt()
        p.flags = int(fl[0])
        p.interp = bool(p.flags & 128)
        p.ttf = 0xFFFF if p.interp else 0
        p.ncp = 0xFFFE
        if len(fl) > 1:
            p.ttf = U16.get(int(fl[1]), int(fl[1])) if fl[1] != "" else 0xFFFE
        if len(fl) > 2:
            p.ncp = U16.get(int(fl[2]), int(fl[2]))
        p.raw_tail = tail
        p.linear_next = False
        p.me = (f32(nums[-2]), f32(nums[-1]))
        p.prevcp = p.me; p.nextcp = p.me
        p.noprevcp = p.nonextcp = True
        if kind == "m":
            cur = [p]
            contours.append(cur)
            continue
        prev = cur[-1]
        if kind == "c":
            prev.nextcp = (f32(nums[0]), f32(nums[1])); prev.nonextcp = False
            p.prevcp = (f32(nums[2]), f32(nums[3])); p.noprevcp = False
        elif kind != "l":
            raise ValueError(ln)
        cur.append(p)
        refigure2(prev, p)
    out = []
    for pts in contours:
        closed = False
        if len(pts) > 1 and pts[-1].me == pts[0].me:     # SFDCloseCheck
            last = pts.pop()
            pts[0].prevcp = last.prevcp; pts[0].noprevcp = last.noprevcp
            closed = True
            refigure2(pts[-1], pts[0])
        out.append((pts, closed, None))
    return out


def transform_point(p, s):
    def t(q):
        x = f32(f32(s) * q[0]); y = f32(f32(s) * q[1])
        x = f32(rint(f32(1024 * x)) / 1024); y = f32(rint(f32(1024 * y)) / 1024)
        return (x, y)
    p.me = t(p.me)
    p.nextcp = t(p.nextcp) if not p.nonextcp else p.me
    p.prevcp = t(p.prevcp) if not p.noprevcp else p.me


def refigure_all(pts, closed):
    n = len(pts)
    for i in range(n if closed else n - 1):
        refigure2(pts[i], pts[(i + 1) % n])


def round_contour(pts, closed):
    """SplineSetsRound2Int / SplinePointRound, factor 1, order2 splines."""
    n = len(pts)
    for i in range(n):
        sp = pts[i]
        has_prev = closed or i > 0
        has_next = closed or i < n - 1
        if has_prev and has_next and sp.ttf == 0xFFFF:
            nx = (rint(sp.nextcp[0]), rint(sp.nextcp[1]))
            pv = (rint(sp.prevcp[0]), rint(sp.prevcp[1]))
            sp.nextcp = (f32(nx[0]), f32(nx[1])); sp.prevcp = (f32(pv[0]), f32(pv[1]))
            sp.me = (f32((sp.nextcp[0] + sp.prevcp[0]) / 2), f32((sp.nextcp[1] + sp.prevcp[1]) / 2))
        else:
            noff = (f32(rint(f32(sp.nextcp[0] - sp.me[0]))), f32(rint(f32(sp.nextcp[1] - sp.me[1]))))
            poff = (f32(rint(f32(sp.prevcp[0] - sp.me[0]))), f32(rint(f32(sp.prevcp[1] - sp.me[1]))))
            sp.me = (f32(rint(sp.me[0])), f32(rint(sp.me[1])))
            sp.nextcp = (f32(sp.me[0] + noff[0]), f32(sp.me[1] + noff[1]))
            sp.prevcp = (f32(sp.me[0] + poff[0]), f32(sp.me[1] + poff[1]))
        # order2: the shared control is copied to the neighbour
        if has_next:
            pts[(i + 1) % n].prevcp = sp.nextcp
        if has_prev:
            pts[(i - 1) % n].nextcp = sp.prevcp
        if sp.nextcp == sp.me:
            sp.nonextcp = True
        if sp.prevcp == sp.me:
            sp.noprevcp = True
        if has_prev:                                   # SplineRefigure(sp->prev)
            refigure2(pts[(i - 1) % n], sp)
    if closed:                                         # SplineRefigure(first->prev)
        refigure2(pts[-1], pts[0])


def dump_splineset(contours):
    """SFDDumpSplineSet: a spline is written as a line when it is linear and its
    end has no control, otherwise as a curve with both (equal) controls."""
    out = []
    for pts, closed, _ in contours:
        seq = pts + ([pts[0]] if closed else [])
        for j, sp in enumerate(seq):
            if j == 0:
                s = "%s %s m " % (g(sp.me[0]), g(sp.me[1]))
            else:
                prev = seq[j - 1]
                if prev.linear_next and sp.noprevcp:
                    s = " %s %s l " % (g(sp.me[0]), g(sp.me[1]))
                else:
                    s = " %s %s %s %s %s %s c " % (g(prev.nextcp[0]), g(prev.nextcp[1]),
                                                  g(sp.prevcp[0]), g(sp.prevcp[1]),
                                                  g(sp.me[0]), g(sp.me[1]))
            out.append(s + sp.raw_tail)
    return out


HDR_RINT = ["LineGap", "VLineGap", "OS2TypoAscent", "OS2TypoDescent", "OS2TypoLinegap",
            "OS2WinAscent", "OS2WinDescent", "HheadAscent", "HheadDescent",
            "OS2SubXSize", "OS2SubYSize", "OS2SubXOff", "OS2SubYOff",
            "OS2SupXSize", "OS2SupYSize", "OS2SupXOff", "OS2SupYOff",
            "OS2StrikeYSize", "OS2StrikeYPos"]


def scale_sfd(text, newem=1024, int_underline=False):
    lines = text.split("\n")
    hdr = {}
    for ln in lines:
        if ln.startswith("BeginChars:"):
            break
        if ":" in ln:
            k, v = ln.split(":", 1)
            hdr.setdefault(k, v.strip())
    ascent, descent = int(hdr["Ascent"]), int(hdr["Descent"])
    oldem = ascent + descent
    ds = newem * descent // oldem          # C int division, all positive here
    as_ = newem - ds
    scale = (as_ + ds) / float(oldem)      # double
    ts = f32(scale)                        # transform[0], a real
    out = []
    i = 0
    in_chars = False
    layer = None
    stats = {"widths": 0, "points": 0, "refs": 0}
    while i < len(lines):
        ln = lines[i]
        if not in_chars:
            k = ln.split(":", 1)[0]
            if ln.startswith("BeginChars:"):
                in_chars = True
            elif k == "Ascent":
                ln = "Ascent: %d" % as_
            elif k == "Descent":
                ln = "Descent: %d" % ds
            elif k in ("UnderlinePosition", "UnderlineWidth"):
                v = f32(f32(float(ln.split(":", 1)[1])) * scale)
                ln = "%s: %s" % (k, ("%d" % rint(v)) if int_underline else g(v))
            elif k in HDR_RINT:
                v = int(ln.split(":", 1)[1])
                ln = "%s: %d" % (k, int(rint(v * scale)))
            out.append(ln); i += 1
            continue
        if ln.startswith("StartChar:"):
            layer = None
        elif ln in ("Fore", "Back") or ln.startswith("Layer: "):
            layer = ln
        elif ln.startswith("Width:") or ln.startswith("VWidth:"):
            k, v = ln.split(":", 1)
            w = int(v)
            nw = f32(f32(w) * ts)
            ln = "%s: %d" % (k, int(nw))        # int16 = real: truncation
            stats["widths"] += 1
        elif ln.startswith("Refer:"):
            t = ln.split()
            e = f32(f32(float(t[8])) * ts); f_ = f32(f32(float(t[9])) * ts)
            if layer == "Fore":
                e, f_ = rint(e), rint(f_)
            t[8], t[9] = g(e), g(f_)
            ln = " ".join(t)
            stats["refs"] += 1
        elif ln == "SplineSet":
            j = i + 1
            while lines[j] != "EndSplineSet":
                j += 1
            contours = parse_splineset(lines[i + 1:j])
            for pts, closed, _ in contours:
                for p in pts:
                    transform_point(p, ts)
                    stats["points"] += 1
                refigure_all(pts, closed)          # SplinePointListTransform
                if layer == "Fore":
                    round_contour(pts, closed)
            out.append(ln)
            out.extend(dump_splineset(contours))
            out.append("EndSplineSet")
            i = j + 1
            continue
        out.append(ln); i += 1
    return "\n".join(out), (as_, ds, scale, stats)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    newem = 1024
    if "--newem" in sys.argv:
        newem = int(sys.argv[sys.argv.index("--newem") + 1])
        args.remove(str(newem))
    src, dst = args
    text = open(src, encoding="latin-1").read()
    new, info = scale_sfd(text, newem, "--int-underline" in sys.argv)
    open(dst, "w", encoding="latin-1").write(new)
    print("%s -> %s  ascent/descent %d/%d scale %.6f  %s" % (src, dst, info[0], info[1], info[2], info[3]))


if __name__ == "__main__":
    main()
