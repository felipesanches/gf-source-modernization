#!/usr/bin/env python3
"""Question answered: does the `sfdlibinterpolated` edit state, in the .sfd itself, exactly
the outline sfdLib 2.0.0 read from the unedited source -- the outline the Comic Relief
release was compiled from -- and does a build of the edited source put every point where
the release has it?

For each glyph the edit touches (Fore layer):

  sfdlib    the unedited .sfd read as sfdLib 2.0.0 reads it (parser.py _drawContours: the
            end point of a quadratic `c` segment flagged 0x80 is an off-curve point, and a
            closed contour's first point is replaced by its closing segment's end), as
            [(x, y, on)] per contour.
  edited    the edited .sfd read as babelfont's SFD reader reads it (pathreading.rs: a
            closed contour drops the move point its closing segment returns to), in TrueType
            order (starting at that point).
  release   the release's glyf points.

Three comparisons, per glyph:
  exact     `edited` without the on-curve points the edit added (flagged 0x80, each
            midway between two off-curve points) == `sfdlib`, where sfdLib starts a
            contour on an off-curve point started at its first on-curve point (where
            ufo2ft's segment pen started the release's): same points, same order, same
            start.
  truetype  both with every on-curve point lying exactly midway between two off-curve
            neighbours dropped, as TrueType implies it and as write-fonts' glyf writer drops
            it (simple.rs is_implicit_on_curve): what fontc writes from either. Equal means
            the build from the edited source equals the build with babelfont's
            --sfdlib-interpolated-points.
  release   the release's points == `sfdlib` rounded as ufo2ft rounds (otRound,
            floor(v + 0.5)), each contour compared as a cycle in either direction (ufo2ft
            reverses contours for TrueType): checks this emulation is what shipped.

Exits 1 if any glyph fails `exact` or `truetype`.

  /home/fsanches/compartilhado/gftools/venv/bin/python3 sfdlib_outline_check.py \\
      <unedited.sfd> <edited.sfd> <release.ttf>
"""
import math
import re
import sys

from fontTools.ttLib import TTFont

SEG = re.compile(r"^ ?((?:-?[\d.]+(?:[eE][-+]?\d+)? )+)([mlc]) (\d+)")


def fore_contours(text):
    """{glyph: (codepoint, [[(x, y, kind, flag, ctrl)]])} from each glyph's Fore SplineSet;
    ctrl = the quadratic control of a `c` segment."""
    out = {}
    for m in re.finditer(r"^StartChar: ([^\n]*)\n(.*?)^EndChar", text, re.M | re.S):
        enc = re.search(r"^Encoding: \S+ (-?\d+) ", m.group(2), re.M)
        ss = re.search(r"^Fore\nSplineSet\n(.*?)^EndSplineSet", m.group(2), re.M | re.S)
        contours = []
        for line in (ss.group(1).splitlines() if ss else []):
            s = SEG.match(line)
            if not s:
                continue
            v = [float(t) for t in s.group(1).split()]
            if s.group(2) == "m":
                contours.append([])
            contours[-1].append((v[-2], v[-1], s.group(2), int(s.group(3)), tuple(v[0:2]) if s.group(2) == "c" else None))
        out[m.group(1)] = (int(enc.group(1)) if enc else -1, contours)
    return out


def sfdlib(contour):
    pts = []
    for x, y, kind, flag, ctrl in contour:
        if kind == "c":
            pts.append((ctrl[0], ctrl[1], False))
            pts.append((x, y, not flag & 0x80))
        else:
            pts.append((x, y, True))
    # closed when the closing segment ends where the contour starts (as written)
    if not any(f & 0x400 for _, _, _, f, _ in contour) and len(pts) > 1 and contour[0][:2] == contour[-1][:2]:
        pts = [pts[-1]] + pts[1:-1]
    return pts


def babelfont_order(contour):
    """[(x, y, on, flag)]: babelfont's nodes of a closed contour, from the closing point."""
    nodes = []
    for x, y, kind, flag, ctrl in contour:
        if kind == "c":
            nodes.append((ctrl[0], ctrl[1], False, 0))
        nodes.append((x, y, True, flag))
    closed = not any(f & 0x400 for _, _, _, f, _ in contour)
    if closed and len(nodes) > 1 and nodes[0][:2] == nodes[-1][:2]:
        nodes = nodes[1:]
    return nodes[-1:] + nodes[:-1]


def drop_implied(nodes, only_flagged=False):
    """Drop each on-curve point exactly midway between two off-curve neighbours (with
    only_flagged, only those flagged 0x80)."""
    n, keep = len(nodes), []
    for i, p in enumerate(nodes):
        a, b = nodes[i - 1], nodes[(i + 1) % n]
        if (p[2] and not a[2] and not b[2] and p[0] == (a[0] + b[0]) / 2 and p[1] == (a[1] + b[1]) / 2
                and (not only_flagged or p[3] & 0x80)):
            continue
        keep.append(p[:3])
    return keep


def same_cycle(a, b):
    """Equal as cycles, in either direction."""
    if len(a) != len(b):
        return False
    if not a:
        return True
    for seq in (b, b[::-1]):
        for k in range(len(seq)):
            if seq[k:] + seq[:k] == a:
                return True
    return False


def ot_round(v):
    return math.floor(v + 0.5)


def main():
    orig, edited, release = sys.argv[1:4]
    o = fore_contours(open(orig, encoding="utf-8", errors="surrogateescape").read())
    e = fore_contours(open(edited, encoding="utf-8", errors="surrogateescape").read())
    f = TTFont(release)
    cmap, glyf = f.getBestCmap(), f["glyf"]
    touched = [g for g in o if any(k == "c" and fl & 0x80 for c in o[g][1] for _, _, k, fl, _ in c)]
    exact, truetype, rel_same, rel_skip, bad = 0, 0, 0, [], []
    for g in touched:
        u, oc = o[g]
        want = [sfdlib(c) for c in oc]
        # as the edit states it: a contour sfdLib starts on an off-curve point started at
        # its first on-curve point, as the release's is (fontTools BasePointToSegmentPen)
        stated = [sfdlib(c) for c in oc]
        stated = [s[next((i for i, p in enumerate(s) if p[2]), 0):] + s[:next((i for i, p in enumerate(s) if p[2]), 0)]
                  for s in stated]
        got = [babelfont_order(c) for c in e[g][1]]
        ok_exact = [drop_implied(c, only_flagged=True) for c in got] == stated
        ok_tt = [drop_implied(c) for c in got] == [drop_implied([p + (0,) for p in c]) for c in stated]
        exact += ok_exact
        truetype += ok_tt
        if not (ok_exact and ok_tt):
            bad.append(g)
        rg = cmap.get(u) if u >= 0 else None
        rg = rg if rg in glyf else (g if g in glyf else None)
        if rg is None or glyf[rg].isComposite():
            rel_skip.append(g)
            continue
        coords, ends, flags = glyf[rg].getCoordinates(glyf)
        rel, start = [], 0
        for end in ends:
            rel.append([(coords[i][0], coords[i][1], bool(flags[i] & 1)) for i in range(start, end + 1)])
            start = end + 1
        rounded = [[(ot_round(x), ot_round(y), on) for x, y, on in c] for c in want]
        if len(rel) == len(rounded) and all(same_cycle(a, b) for a, b in zip(rounded, rel)):
            rel_same += 1
    print("%s: %d glyphs touched; exact %d, truetype %d; release == otRound(sfdLib) in %d of %d "
          "(%d not comparable: composite or absent)%s" % (
              edited, len(touched), exact, truetype, rel_same, len(touched) - len(rel_skip), len(rel_skip),
              "; DIFFER: " + " ".join(bad) if bad else ""))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
