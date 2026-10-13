#!/usr/bin/env python3
"""Question answered: when the table gate reports GDEF.glyph_classes, do the two fonts give
different glyphs different classes, or do they only NAME the glyphs differently?

The gate (through diffenator3) compares classes by glyph name. A release with no glyph names
(post format 3) is named by fontTools (AGL names for encoded glyphs) while the build names them
uniXXXX, so every renamed glyph reads as "class in the release, none in ours". This prints the
per-class counts, the class transitions by name, the same comparison by glyph id (classes and
mark attachment classes), and which lookup flags each font uses.

  python3 gdef_classes.py <release.ttf> <build.ttf>
"""
import collections
import sys

from fontTools.ttLib import TTFont

fonts = [TTFont(p) for p in sys.argv[1:3]]


def classes(font, attr):
    gdef = font.get("GDEF")
    cd = getattr(gdef.table, attr, None) if gdef else None
    return dict(cd.classDefs) if cd else {}


for attr in ("GlyphClassDef", "MarkAttachClassDef"):
    a, b = (classes(f, attr) for f in fonts)
    print("%s: release %s, build %s" % (attr, dict(collections.Counter(a.values())),
                                        dict(collections.Counter(b.values()))))
    by_name = collections.Counter((a.get(n, 0), b.get(n, 0)) for n in fonts[0].getGlyphOrder()
                                  if a.get(n, 0) != b.get(n, 0))
    print("  by name, release -> build class: %s" % dict(by_name))
    ga = [a.get(n, 0) for n in fonts[0].getGlyphOrder()]
    gb = [b.get(n, 0) for n in fonts[1].getGlyphOrder()]
    differ = sum(x != y for x, y in zip(ga, gb)) + abs(len(ga) - len(gb))
    print("  by glyph id: %s" % ("equal" if differ == 0 else "%d differ" % differ))
for path, font in zip(sys.argv[1:3], fonts):
    print("%s: post format %s" % (path, font["post"].formatType))
    for tag in ("GSUB", "GPOS"):
        if tag in font:
            flags = collections.Counter(hex(lk.LookupFlag) for lk in font[tag].table.LookupList.Lookup)
            print("  %s lookup flags: %s" % (tag, dict(flags)))
