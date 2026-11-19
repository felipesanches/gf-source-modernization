#!/usr/bin/env python3
"""Question: are a release's vmtx and GSUB equal to a build's glyph index by index, when the
release stores no glyph names (post format 3) and the names therefore differ?
Usage: by_index.py <release.ttf> <build.ttf>   (fontTools from the gftools venv)"""
import io
import sys
from fontTools.misc.xmlWriter import XMLWriter
from fontTools.ttLib import TTFont


def by_gid(path, tag):
    f = TTFont(path, lazy=True)
    f.setGlyphOrder(["gid%d" % i for i in range(f["maxp"].numGlyphs)])
    if tag not in f:
        return None
    buf = io.StringIO()
    f[tag].toXML(XMLWriter(buf), f)
    return buf.getvalue()


rel, bld = sys.argv[1:3]
names = TTFont(rel, lazy=True)["post"].formatType, TTFont(bld, lazy=True)["post"].formatType
print("post format: release %s, build %s" % names)
for tag in ("vmtx", "GSUB", "hmtx"):
    a, b = by_gid(rel, tag), by_gid(bld, tag)
    print("%s by glyph index: %s" % (tag, "equal" if a == b else "DIFFERENT"))
