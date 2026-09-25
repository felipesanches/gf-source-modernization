#!/usr/bin/env python3
"""Question answered: at what threshold does a per-glyph rendering comparison separate the
outline differences the conversion is known to introduce (FontForge vs babelfont rounding:
at most 1 font unit, implied on-curve points kept or dropped, contour start point) from real
ones, and does diffenator3's own glyph threshold (32 ppem, gray fuzz 8, > 16 px) see a
local deformation at all?

For every glyph both fonts have whose normalised outline (functional_gate.Font.outline)
differs, FreeType renders it unhinted twice per font:
  d3-like   32 ppem, count pixels whose gray differs by > 8 (diffenator3 1.1.4's glyph test)
  geometry  ppem = unitsPerEm / 8 (1 px = 8 font units), count pixels whose coverage differs
            by > 64/255 (a quarter pixel = 2 font units of edge displacement)
and records, per pair, how many changed glyphs reach each pixel count, plus the worst glyphs.

Usage: $PY tools/probes/functional_gate/calibrate_geometry.py [pairs.tsv] > tools/probes/functional_gate/CALIBRATION.txt
Without an argument the pairs are validate.py's (every landed style, built there if missing,
and EXTRA.tsv), plus mutations.py's moved-point copy of Salsa-Regular when it exists.
pairs.tsv, if given: repo<TAB>style<TAB>shipped<TAB>built per line.
"""
import collections
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import freetype  # noqa: E402
import functional_gate as fg  # noqa: E402


def counts(A, B, n, nb, face_a, face_b, fuzz):
    return fg.bitmap_diff(fg.ft_bitmap(face_a, A.gid[n]), fg.ft_bitmap(face_b, B.gid[nb]), fuzz)


def mutations_release():
    import mutations
    return mutations.REL


def main():
    buckets = (0, 1, 2, 4, 8, 16, 32, 64, 10 ** 9)
    if len(sys.argv) > 1:
        pairs = [line.rstrip("\n").split("\t")[:4] for line in open(sys.argv[1]) if line.strip()]
    else:
        import validate
        pairs = [j[:4] for j in validate.jobs()]
        moved = os.path.join(fg.SCRATCH, "mutations", "unencoded.ttf")
        if os.path.exists(moved):
            pairs.append(["mutation", "Salsa-unencoded-point+60", mutations_release(), moved])
    for repo, style, shipped, built in pairs:
        A, B = fg.Font(shipped), fg.Font(built)
        _, _, ka, kb = fg.correspondence(A, B)
        inv_b = {k: n for n, k in kb.items()}
        f32a, f32b = freetype.Face(shipped), freetype.Face(built)
        f32a.set_pixel_sizes(0, 32)
        f32b.set_pixel_sizes(0, 32)
        gpa, gpb = freetype.Face(shipped), freetype.Face(built)
        ppem = max(8, round(A.upem / 8))
        gpa.set_pixel_sizes(0, ppem)
        gpb.set_pixel_sizes(0, ppem)
        d3like, geo = collections.Counter(), collections.Counter()
        worst = []
        changed = 0
        for n in sorted(A.reachable()):
            nb = inv_b.get(ka[n])
            if nb is None or A.outline(n) == B.outline(nb):
                continue
            changed += 1
            x = counts(A, B, n, nb, f32a, f32b, 8)
            y = counts(A, B, n, nb, gpa, gpb, 64)
            for lo, hi in zip(buckets, buckets[1:]):
                if lo <= x < hi or (lo == 0 and x == 0):
                    d3like["%d-%d" % (lo, hi - 1) if hi < 10 ** 9 else ">=%d" % lo] += 1
                    break
            for lo, hi in zip(buckets, buckets[1:]):
                if lo <= y < hi:
                    geo["%d-%d" % (lo, hi - 1) if hi < 10 ** 9 else ">=%d" % lo] += 1
                    break
            worst.append((y, x, n))
        worst.sort(reverse=True)
        print("%-28s changed %4d | d3-like(32ppem,fuzz8) %s | geometry(%dppem,fuzz64) %s | worst %s" % (
            style, changed, dict(sorted(d3like.items())), ppem, dict(sorted(geo.items())),
            ", ".join("%s geo%d/d3like%d" % (n, y, x) for y, x, n in worst[:4])))
        sys.stdout.flush()


if __name__ == "__main__":
    main()
