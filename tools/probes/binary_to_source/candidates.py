#!/usr/bin/env python3
"""Question answered: which families the library census lists as having no source anywhere
are the next candidates for a source converted from their binaries, and what in each one
the conversion will have to get right?

For every NO-SOURCES family of the census (sfd-batch5/library_state_census.tsv) with .ttf
files in the google/fonts checkout: styles, hinting (none / ttfautohint / other fpgm),
variable or not, legacy kern table, GPOS, GDEF, the most glyphs in a style, and whether its
upstream_info.md names a place a source may live (Launchpad, Bazaar, SourceForge, a .sfd/
.vfb/.ufo/.glyphs file) -- Della Respira's did, and its source was on Launchpad.

Usage: candidates.py <census tsv> <google/fonts checkout>    (TSV on stdout)
"""
import glob
import os
import re
import sys

from fontTools.ttLib import TTFont

HINT_OF_SOURCE = re.compile(r"launchpad|bazaar|\bbzr\b|sourceforge|\.sfd\b|\.vfb\b|\.ufo\b|\.glyphs\b",
                            re.I)


def main():
    census, gf = sys.argv[1], sys.argv[2]
    rows = [l.split("\t") for l in open(census).read().splitlines()[1:]]
    families = sorted(r[0] for r in rows if len(r) > 2 and r[2] == "NO-SOURCES")
    print("family\tlic\tstyles\thinting\tvariable\tkern\tgpos\tgdef\tglyphs\tsource_hint")
    for fam in families:
        d = [x for x in glob.glob(os.path.join(gf, "*", fam)) if os.path.isdir(x)]
        ttfs = sorted(glob.glob(os.path.join(d[0], "*.ttf"))) if d else []
        if not ttfs:
            continue
        hints, var, kern, gpos, gdef, glyphs = set(), False, False, False, False, 0
        for p in ttfs:
            t = TTFont(p, lazy=True)
            h = "ttfautohint" if "TTFA" in t or "ttfautohint" in (t["name"].getDebugName(5) or "") \
                else "fpgm" if "fpgm" in t else "none"
            hints.add(h)
            var |= "fvar" in t
            kern |= "kern" in t
            gpos |= "GPOS" in t
            gdef |= "GDEF" in t
            glyphs = max(glyphs, t["maxp"].numGlyphs)
        info = os.path.join(d[0], "upstream_info.md")
        text = open(info, encoding="utf-8", errors="replace").read() if os.path.exists(info) else ""
        found = sorted({m.lower() for m in HINT_OF_SOURCE.findall(text)})
        print("\t".join([fam, d[0].split(os.sep)[-2], str(len(ttfs)), "/".join(sorted(hints)),
                         str(int(var)), str(int(kern)), str(int(gpos)), str(int(gdef)),
                         str(glyphs), ",".join(found)]))


if __name__ == "__main__":
    main()
