#!/usr/bin/env python3
"""Adversarial verification, unit "tuffy".

Question it answers: which composite glyphs place their components differently in
font B than in font A? Every glyph is flattened to its leaf (outline) components
with absolute offsets; leaf names are mapped between the fonts by codepoint (the
two fonts name glyphs differently: uniXXXX vs AGL names), falling back to the name.
Advance is compared too.

Usage: component_moves.py <A.ttf> <B.ttf>
Prints one line per codepoint whose flattened placement or advance differs.
"""
import sys
from fontTools.ttLib import TTFont


def flat(font, name, dx=0, dy=0):
    g = font["glyf"][name]
    if not g.isComposite():
        return [(name, dx, dy)]
    out = []
    for c in g.components:
        out += flat(font, c.glyphName, dx + c.x, dy + c.y)
    return out


def main():
    A, B = TTFont(sys.argv[1]), TTFont(sys.argv[2])
    ca, cb = A.getBestCmap(), B.getBestCmap()
    # leaf-name translation A -> B through the cmap
    rev_a = {}
    for cp, n in sorted(ca.items()):
        rev_a.setdefault(n, cp)
    tr = {n: cb.get(cp, n) for n, cp in rev_a.items()}
    n = 0
    for cp in sorted(set(ca) & set(cb)):
        na, nb = ca[cp], cb[cp]
        ga, gb = A["glyf"][na], B["glyf"][nb]
        if not (ga.isComposite() or gb.isComposite()):
            continue
        fa = sorted((tr.get(x, x), X, Y) for x, X, Y in flat(A, na))
        fb = sorted(flat(B, nb))
        wa, wb = A["hmtx"][na][0], B["hmtx"][nb][0]
        if fa != fb or wa != wb:
            n += 1
            print("U+%04X %-26s adv %5d -> %5d  A %s  B %s" % (cp, na, wa, wb, fa, fb))
    print("%d composite codepoint(s) differ" % n)


if __name__ == "__main__":
    main()
