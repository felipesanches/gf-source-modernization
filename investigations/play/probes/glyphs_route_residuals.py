#!/usr/bin/env python3
"""Question answered: what exactly differs between the Play google/fonts ships and a
build of alexeiva/play sources/Play.glyphs (d84ad58) through gftools-builder's static
path (glyphslib -> babelfont instancer -> fontc), for the residual classes listed in
../README-glyphs-route.md? One line per class, for one style.

Usage: python3 glyphs_route_residuals.py <shipped.ttf> <built.ttf>
"""
import sys
import uharfbuzz as hb
from fontTools.ttLib import TTFont

rel_p, bld_p = sys.argv[1:3]
R, B = TTFont(rel_p), TTFont(bld_p)


def langsys(f):
    gs = f["GSUB"].table
    return {sr.ScriptTag: sorted({gs.FeatureList.FeatureRecord[i].FeatureTag
                                  for i in sr.Script.DefaultLangSys.FeatureIndex})
            for sr in gs.ScriptList.ScriptRecord}


def shape(path, text):
    font = hb.Font(hb.Face(hb.Blob.from_file_path(path)))
    buf = hb.Buffer(); buf.add_str(text); buf.guess_segment_properties(); hb.shape(font, buf, {})
    return " ".join(font.glyph_to_string(i.codepoint) for i in buf.glyph_infos)


for name, f in (("release", R), ("build", B)):
    print("== %s" % name)
    print("  GSUB default langsys features: %s" % langsys(f))
    print("  shape 'office': %s" % shape(rel_p if f is R else bld_p, "office"))
    g = f["glyf"]["acutecomb"]
    print("  acutecomb advance %s xMin..xMax %s..%s" % (f["hmtx"]["acutecomb"][0], g.xMin, g.xMax))
    print("  OS/2 usWeightClass %s panose bWeight %s; post underlinePosition %s thickness %s"
          % (f["OS/2"].usWeightClass, f["OS/2"].panose.bWeight, f["post"].underlinePosition,
             f["post"].underlineThickness))
    print("  name 4/6: %s" % [n.toUnicode() for n in f["name"].names
                               if n.platformID == 3 and n.nameID in (4, 6)])
    gd = f["GDEF"].table
    print("  GDEF %s MarkAttachClassDef %s MarkGlyphSets %s; GPOS lookup flags %s"
          % (hex(gd.Version), len(gd.MarkAttachClassDef.classDefs) if gd.MarkAttachClassDef else None,
             len(gd.MarkGlyphSetsDef.Coverage) if getattr(gd, "MarkGlyphSetsDef", None) else None,
             sorted({l.LookupFlag for l in f["GPOS"].table.LookupList.Lookup})))
    cmap = f.getBestCmap()
    print("  names at U+0122 U+0306 U+000D: %s; U+FB00/FB03/FB04 mapped: %s"
          % ([cmap.get(c) for c in (0x122, 0x306, 0xD)], [c in cmap for c in (0xFB00, 0xFB03, 0xFB04)]))
    gl = f["glyf"][cmap[0x122]]
    print("  U+0122 points %d bbox %s" % (len(gl.getCoordinates(f["glyf"])[0]), (gl.xMin, gl.yMin, gl.xMax, gl.yMax)))
