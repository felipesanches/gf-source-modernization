#!/usr/bin/env python3
"""Compare Allerta Regular builds with the shipped font: which tables differ between the two
builds, and per build the glyph names, outlines (point by point, so a changed start point
counts), outline bounds (a real change of shape), advances, kept composites and post underline values against the shipped font.

Usage: compare.py <shipped.ttf> <build at bdd9557> <build at the new commit>
"""
import io
import sys
from fontTools.pens.recordingPen import RecordingPen
from fontTools.ttLib import TTFont

shipped, old, new = (TTFont(p) for p in sys.argv[1:4])
SKIP = ("checkSumAdjustment", "modified", "created", "<ttFont")


def xml(font, tag):
    out = io.StringIO()
    font.saveXML(out, tables=[tag])
    return [l for l in out.getvalue().splitlines() if not any(s in l for s in SKIP)]


print("tables that differ between the builds:",
      [t for t in sorted(set(old.keys()) | set(new.keys()))
       if t != "GlyphOrder" and (t not in old or t not in new or xml(old, t) != xml(new, t))])


def bounds(glyphset, name):
    from fontTools.pens.boundsPen import BoundsPen
    pen = BoundsPen(glyphset)
    glyphset[name].draw(pen)
    return pen.bounds


def outline(glyphset, name):
    pen = RecordingPen()
    glyphset[name].draw(pen)
    return pen.value


ref = shipped.getGlyphSet()
for label, font in (("bdd9557", old), ("new", new)):
    gs = font.getGlyphSet()
    names = [g for g in shipped.getGlyphOrder() if g in gs]
    print("%s: glyph names as shipped %s; outlines differ %d of %d (bounds %d); advances differ %d; "
          "composites %d; post underline %s (shipped %s)" % (
              label, font.getGlyphOrder() == shipped.getGlyphOrder(),
              sum(outline(ref, g) != outline(gs, g) for g in names), len(names),
              sum(bounds(ref, g) != bounds(gs, g) for g in names),
              sum(shipped["hmtx"][g][0] != font["hmtx"][g][0] for g in names),
              sum(font["glyf"][g].isComposite() for g in font.getGlyphOrder()),
              (font["post"].underlinePosition, font["post"].underlineThickness),
              (shipped["post"].underlinePosition, shipped["post"].underlineThickness)))
