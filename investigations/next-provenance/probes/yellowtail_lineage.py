#!/usr/bin/env python3
"""Where does the Yellowtail binary Google Fonts ships come from?

Question answered: the only file named .sfd in the monorepo
(apache/yellowtail/src/Yellowtail-Regular-TTF.sfd) is not an SFD. Is the shipped
Yellowtail-Regular.ttf (google/fonts b5efa9c32e8f) a FontForge export of the designer's
TrueType (hg f66bfe1e9 yellowtail/Yellowtail-Regular.ttf), of the designer's OTF
(hg src/Yellowtail-Regular.otf), or of something else -- and what did each later step
(hg 60268f00f, Dave Crossland 2011-07-18 "stripping hints and using the magic values";
google/fonts 1baf54ea4, PR #803 "hotfix-yellowtail: v1.002") change?

For each consecutive pair it prints the tables that differ, the name records that
differ, and, per glyph, whether the outline points are identical. For the designer TTF vs
the FontForge export it also reports whether kerning survived.

Usage (extracts every file itself from the archive and google/fonts):
  /home/fsanches/compartilhado/gftools/venv/bin/python3 yellowtail_lineage.py
"""
import io
import subprocess

from fontTools.ttLib import TTFont

ARC = "/home/fsanches/compartilhado/upstream_repos/repo_archive/googlefonts/googlefontdirectory-hg.git"
GF = "/home/fsanches/compartilhado/google/fonts"


def blob(repo, rev, path):
    return subprocess.run(["git", "-C", repo, "show", "%s:%s" % (rev, path)],
                          capture_output=True, check=True).stdout


FONTS = [
    ("designer TTF (hg f66bfe1e9)", TTFont(io.BytesIO(blob(ARC, "f66bfe1e9", "yellowtail/Yellowtail-Regular.ttf")))),
    ("designer OTF (hg f66bfe1e9)", TTFont(io.BytesIO(blob(ARC, "f66bfe1e9", "yellowtail/src/Yellowtail-Regular.otf")))),
    ("FontForge 20110222 export (hg 60268f00f)", TTFont(io.BytesIO(blob(ARC, "60268f00f", "yellowtail/Yellowtail-Regular.ttf")))),
    ("google/fonts 2015 import (90abd17b4)", TTFont(io.BytesIO(blob(GF, "90abd17b4", "apache/yellowtail/Yellowtail-Regular.ttf")))),
    ("google/fonts v1.002 (1baf54ea4 = b5efa9c32e8f)", TTFont(io.BytesIO(blob(GF, "b5efa9c32e8f", "apache/yellowtail/Yellowtail-Regular.ttf")))),
]


def points(font, name):
    gs = font["glyf"][name] if "glyf" in font else None
    if gs is None:
        return None
    if gs.isComposite():
        return ("composite", tuple((c.glyphName, c.x, c.y) for c in gs.components))
    if gs.numberOfContours == 0:
        return ()
    coords, ends, flags = gs.getCoordinates(font["glyf"])
    return (tuple(coords), tuple(ends), tuple(f & 1 for f in flags))


def compare(la, a, lb, b):
    print("== %s  ->  %s" % (la, lb))
    ta = set(a.keys()) - {"GlyphOrder"}
    tb = set(b.keys()) - {"GlyphOrder"}
    print("  tables only before:", sorted(ta - tb), " only after:", sorted(tb - ta))
    same = [t for t in sorted(ta & tb) if a.reader[t] == b.reader[t]]
    print("  byte-identical tables:", same)
    na = {(r.nameID, r.platformID, r.langID): r.toUnicode() for r in a["name"].names}
    nb = {(r.nameID, r.platformID, r.langID): r.toUnicode() for r in b["name"].names}
    for k in sorted(set(na) | set(nb)):
        if na.get(k) != nb.get(k):
            print("  name %s: %r -> %r" % (k, (na.get(k) or "")[:60], (nb.get(k) or "")[:60]))
    if "glyf" in a and "glyf" in b:
        ca, cb = a.getBestCmap(), b.getBestCmap()
        diff = same_n = 0
        examples = []
        for cp in sorted(set(ca) & set(cb)):
            pa, pb = points(a, ca[cp]), points(b, cb[cp])
            if pa == pb:
                same_n += 1
            else:
                diff += 1
                if len(examples) < 5:
                    examples.append("U+%04X" % cp)
        print("  outlines by codepoint: %d identical, %d differ %s; cmap only before %s, only after %s" % (
            same_n, diff, examples, ["U+%04X" % c for c in sorted(set(ca) - set(cb))],
            ["U+%04X" % c for c in sorted(set(cb) - set(ca))]))
        wa, wb = a["hmtx"].metrics, b["hmtx"].metrics
        adv = sum(1 for cp in set(ca) & set(cb) if wa[ca[cp]][0] != wb[cb[cp]][0])
        print("  advances differing by codepoint: %d" % adv)
    for t in ("kern", "GPOS"):
        print("  %s: before %s, after %s" % (t, t in a, t in b))


if __name__ == "__main__":
    compare(*FONTS[0], *FONTS[2])
    compare(*FONTS[2], *FONTS[3])
    compare(*FONTS[3], *FONTS[4])
    o = FONTS[1][1]
    print("== designer OTF: CFF charstrings, %d glyphs, cmap %d, GPOS %s -- cubic, so it cannot be the"
          " source of a glyf identical to the designer TTF's" % (len(o.getGlyphOrder()), len(o.getBestCmap()), "GPOS" in o))
