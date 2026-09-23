#!/usr/bin/env python3
"""Question answered: does the em-scaled .sfd written by ff_scale_em.py hold, point
for point, the outlines google/fonts ships -- i.e. is the release exactly this
source after FontForge's `f.em = 1024`?

For every glyph it emits the TrueType points FontForge 20100501's exporter would
write from the scaled .sfd (tottf.c SSAddPoints: an on-curve point numbered -1
in the .sfd is omitted when SPInterpolate() holds -- midway between its two
controls within .1 and not flagged dontinterpolate; a control is written when
the .sfd numbered it, or when it is not collapsed onto its point) and compares them
with the release's glyf: same contours, same points in the same cyclic order,
same on/off flags, same coordinates. Composites: same components and offsets.
Advance widths are compared from the .sfd Width lines.

Usage: verify_scaled_points.py <scaled.sfd> <release.ttf>
Prints a summary line: glyphs compared, exact, differing (with the first few).
"""
import sys

from fontTools.ttLib import TTFont

sys.path.insert(0, __import__("os").path.dirname(__file__))
from ff_scale_em import parse_splineset  # noqa: E402


def within(a, b, d):
    return abs(a - b) <= d


def spinterpolate(sp):
    dont = bool(sp.flags & 256)
    roundx, roundy = bool(sp.flags & 32), bool(sp.flags & 64)
    return (not dont and not sp.nonextcp and not sp.noprevcp and not roundx and not roundy
            and within(sp.me[0], (sp.nextcp[0] + sp.prevcp[0]) / 2, .1)
            and within(sp.me[1], (sp.nextcp[1] + sp.prevcp[1]) / 2, .1))


def emit(contours):
    """tottf.c: SSTtfNumberPoints (renumber, deciding which on-curve points are
    implied and which controls keep a slot) then SSAddPoints (emit)."""
    out = []
    pnum = 0
    for pts, closed, _ in contours:
        n = len(pts)
        first = pts[0]
        prev_of_first = pts[-1] if closed else None
        swc = (not first.noprevcp and
               ((first.ttf == pnum + 1 and prev_of_first is not None and prev_of_first.ncp == pnum)
                or spinterpolate(first)))
        if swc and prev_of_first is not None:
            prev_of_first.ncp = pnum; pnum += 1
        for i, sp in enumerate(pts):
            if spinterpolate(sp):
                sp.ttf = 0xFFFF
            else:
                sp.ttf = pnum; pnum += 1
            if sp.nonextcp and sp.ncp != pnum:
                sp.ncp = 0xFFFF
            elif not swc or (i < n - 1):
                sp.ncp = pnum; pnum += 1
            if i == n - 1:
                break
    ptcnt = 0
    for pts, closed, _ in contours:
        n = len(pts)
        seq = []
        startcnt = ptcnt
        first = pts[0]
        if closed and pts[-1].ncp == startcnt:
            seq.append((round(first.prevcp[0]), round(first.prevcp[1]), 0)); ptcnt += 1
        for i, sp in enumerate(pts):
            if sp.ttf != 0xFFFF or not spinterpolate(sp):
                seq.append((round(sp.me[0]), round(sp.me[1]), 1)); ptcnt += 1
            if sp.ncp == startcnt:
                break
            if i == n - 1 and not closed:
                break
            if sp.ncp not in (0xFFFF, 0xFFFE) or not sp.nonextcp:
                seq.append((round(sp.nextcp[0]), round(sp.nextcp[1]), 0)); ptcnt += 1
        out.append(seq)
    return out


def canon(seq):
    if not seq:
        return tuple()
    rots = [tuple(seq[i:] + seq[:i]) for i in range(len(seq))]
    return min(rots)


def read_sfd(path):
    lines = open(path, encoding="latin-1").read().split("\n")
    glyphs = {}
    name = None
    layer = None
    gid_names = {}
    i = 0
    while i < len(lines):
        ln = lines[i]
        if ln.startswith("StartChar:"):
            name = ln.split(":", 1)[1].strip()
            glyphs[name] = {"contours": [], "refs": [], "width": None}
            layer = None
        elif ln.startswith("Encoding:") and name:
            gid_names[int(ln.split()[3])] = name
        elif ln.startswith("Width:") and name:
            glyphs[name]["width"] = int(ln.split()[1])
        elif ln in ("Fore", "Back"):
            layer = ln
        elif ln.startswith("Refer:") and layer == "Fore":
            t = ln.split()
            glyphs[name]["refs"].append((int(t[1]), float(t[8]), float(t[9])))
        elif ln == "SplineSet":
            j = i + 1
            while lines[j] != "EndSplineSet":
                j += 1
            if layer == "Fore":
                glyphs[name]["contours"] = parse_splineset(lines[i + 1:j])
            i = j
        elif ln == "EndChar":
            name = None
        i += 1
    for g in glyphs.values():
        g["refs"] = [(gid_names.get(r[0], "?%d" % r[0]), r[1], r[2]) for r in g["refs"]]
    return glyphs


def main():
    sfd, rel = sys.argv[1:3]
    glyphs = read_sfd(sfd)
    f = TTFont(rel)
    glyf, hmtx = f["glyf"], f["hmtx"].metrics
    exact = 0
    bad = []
    widths_bad = []
    for name, g in glyphs.items():
        if name not in glyf:
            bad.append((name, "absent from release"))
            continue
        if hmtx[name][0] != g["width"]:
            widths_bad.append((name, g["width"], hmtx[name][0]))
        rg = glyf[name]
        if rg.isComposite():
            rc = sorted((c.glyphName, c.x, c.y) for c in rg.components)
            mc = sorted((n, round(x), round(y)) for n, x, y in g["refs"])
            if rc == mc and not g["contours"]:
                exact += 1
            else:
                bad.append((name, "components %s vs release %s" % (mc, rc)))
            continue
        if g["refs"]:
            bad.append((name, "sfd has refs+contours, release simple"))
            continue
        mine = emit(g["contours"])
        coords, ends, flags = [], [], []
        if rg.numberOfContours > 0:
            coords, ends, flags = rg.getCoordinates(glyf)
        theirs, start = [], 0
        for e in (ends if rg.numberOfContours > 0 else []):
            theirs.append([(coords[k][0], coords[k][1], flags[k] & 1) for k in range(start, e + 1)])
            start = e + 1
        if [canon(c) for c in mine] == [canon(c) for c in theirs]:
            exact += 1
        else:
            # measure the worst coordinate difference when structure agrees
            note = "structure differs"
            if len(mine) == len(theirs) and all(len(a) == len(b) for a, b in zip(mine, theirs)):
                worst = 0
                for a, b in zip(mine, theirs):
                    ca, cb = canon(a), None
                    best = None
                    for r in range(len(b)):
                        rb = b[r:] + b[:r]
                        if [p[2] for p in rb] != [p[2] for p in a]:
                            continue
                        d = max(max(abs(p[0] - q[0]), abs(p[1] - q[1])) for p, q in zip(a, rb))
                        best = d if best is None else min(best, d)
                    worst = max(worst, best if best is not None else 99999)
                note = "same structure, worst coordinate difference %s" % worst
            bad.append((name, note))
    print("%s: %d glyphs, %d exact, %d differ; advance widths differing: %d"
          % (sfd.split("/")[-1], len(glyphs), exact, len(bad), len(widths_bad)))
    for b in bad[:12]:
        print("   ", b)
    for w in widths_bad[:6]:
        print("    width", w)
    return 1 if bad or widths_bad else 0


if __name__ == "__main__":
    sys.exit(main())
