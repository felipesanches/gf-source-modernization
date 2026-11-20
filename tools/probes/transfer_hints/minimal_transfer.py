#!/usr/bin/env python3
"""Question answered: how far does the minimal `gftools transfer-hints` Marc proposed on
gftools#1248 (2026-11-16) get a build to the release's hinting? "Transfer the gasp, fpgm and
other whole tables; then for matching glyphs only transfer the instructions if the direction
and point counts match."

This is that rule, nothing more: copy fpgm, prep, cvt, gasp and maxp's hinting limits from the
release; for each glyph the release instructs (paired by name), copy its program when the
built glyph has the same number of contours, the same point count per contour and the same
direction per contour (a composite: the same number of components); otherwise leave the glyph
uninstructed. Then run tools/functional_gate.py's hinting check on the result.

Counts per font: instructed glyphs in the release; transferred; refused (point counts or
contours differ / direction differs / composite differs); and, among the transferred, how many
land on points that are not the release's (same counts, other coordinates or order), where a
program addresses the wrong points.

Usage: minimal_transfer.py <release.ttf> <built.ttf> <out.ttf>
"""
import os
import sys

from fontTools.ttLib import TTFont

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import functional_gate as fg  # noqa: E402

TABLES = ("fpgm", "prep", "cvt ", "gasp")
MAXP = ("maxZones", "maxTwilightPoints", "maxStorage", "maxFunctionDefs", "maxInstructionDefs",
        "maxStackElements", "maxSizeOfInstructions")


def program(g):
    p = getattr(g, "program", None)
    return p if p is not None and p.getBytecode() else None


def contours(glyf, g):
    coords, ends, _ = g.getCoordinates(glyf)
    out, start = [], 0
    for e in ends:
        pts = list(coords[start:e + 1])
        area = sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]))
        out.append((len(pts), area > 0))
        start = e + 1
    return out


def main():
    rel_path, built_path, out_path = sys.argv[1:4]
    rel, built = TTFont(rel_path), TTFont(built_path)
    for t in TABLES:
        if t in rel:
            built[t] = rel[t]
        elif t in built and t != "gasp":
            del built[t]
    for f in MAXP:
        setattr(built["maxp"], f, getattr(rel["maxp"], f))
    rg, bg = rel["glyf"], built["glyf"]
    n = {"instructed": 0, "transferred": 0, "refused: points/contours": 0, "refused: direction": 0,
         "refused: composite": 0, "missing": 0, "transferred on moved points": 0}
    for name in rel.getGlyphOrder():
        a = rg[name]
        if program(a) is None:
            continue
        n["instructed"] += 1
        if name not in bg:
            n["missing"] += 1
            continue
        b = bg[name]
        if a.isComposite() or b.isComposite():
            if not (a.isComposite() and b.isComposite() and len(a.components) == len(b.components)):
                n["refused: composite"] += 1
                continue
        else:
            ca, cb = contours(rg, a), contours(bg, b)
            if [c for c, _ in ca] != [c for c, _ in cb]:
                n["refused: points/contours"] += 1
                continue
            if [d for _, d in ca] != [d for _, d in cb]:
                n["refused: direction"] += 1
                continue
            if list(a.getCoordinates(rg)[0]) != list(b.getCoordinates(bg)[0]):
                n["transferred on moved points"] += 1
        b.program = a.program
        n["transferred"] += 1
    built.save(out_path)
    A, B = fg.Font(rel_path), fg.Font(out_path)
    _, _, ka, kb = fg.correspondence(A, B)
    res = fg.check_hinting(A, B, ka, kb, 3)
    print("  " + "; ".join("%s %d" % kv for kv in n.items()))
    print("  hinting check: %s %s" % (res["status"], res["summary"][:160]))
    for f in res["failures"][:3]:
        print("    - " + f[:160])


if __name__ == "__main__":
    main()
