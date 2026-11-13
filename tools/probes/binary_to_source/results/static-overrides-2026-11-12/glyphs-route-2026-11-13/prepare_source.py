#!/usr/bin/env python3
"""Question: what must be added to a single-master split of itfoundry/kumar's Glyphs file
(551e277f) before gftools can build the shipped Kumar One / Kumar One Outline from it?

Usage: prepare_source.py <split .glyphs> <repo features dir> <shipped .ttf> <out .glyphs>
Each step below is one edit the upstream source lacks (hindkit + AFDKO supplied it at build
time); the script prints them. Nothing is drawn or re-spaced.
"""
import sys
import glyphsLib
from glyphsLib.classes import GSInstance, GSFeaturePrefix, GSCustomParameter
from fontTools.ttLib import TTFont

src, feadir, shipped, out = sys.argv[1:5]
f = glyphsLib.GSFont(src)
t = TTFont(shipped)
edits = []

# 1. an exported instance (the file has none)
inst = GSInstance(); inst.name = "Regular"; inst.weight = "Regular"
inst.axes = list(f.masters[0].axes)
f.instances = [inst]
edits.append("instance Regular added")

# 2. glyph names: the four names GlyphOrderAndAliasDB changes
ren = {"Acaron": "uni01CD", "acaron": "uni01CE", "Ocaron": "uni01D1", "ocaron": "uni01D2"}
for g in f.glyphs:
    if g.name in ren:
        g.name = ren[g.name]
for g in f.glyphs:
    for layer in g.layers:
        for c in layer.components:
            if c.name in ren:
                c.name = ren[c.name]
edits.append("4 glyphs renamed as GlyphOrderAndAliasDB does: %s" % ren)

# 3. codepoints: the shipped cmap
cmap = t.getBestCmap(); want = {}
for cp, name in cmap.items():
    want.setdefault(name, []).append("%04X" % cp)
changed = []
for g in f.glyphs:
    have = sorted(g.unicodes or ([g.unicode] if g.unicode else []))
    new = sorted(want.get(g.name, []))
    if have != new:
        changed.append((g.name, have, new)); g.unicodes = new
edits.append("codepoints changed on %d glyphs: %s" % (len(changed), changed))

# 4. glyph order: the shipped one
order = [n for n in t.getGlyphOrder()]
f.customParameters.append(GSCustomParameter("glyphOrder", order))
edits.append("glyphOrder parameter: the shipped order")

# 5. features: the repository's two GSUB files, behind the shipped language systems
fea = "languagesystem DFLT dflt;\nlanguagesystem gjr2 dflt;\nlanguagesystem gujr dflt;\n\n"
fea += open(feadir + "/GSUB_lookups.fea").read() + "\n" + open(feadir + "/GSUB.fea").read()
p = GSFeaturePrefix(); p.name = "GSUB"; p.code = fea
f.featurePrefixes.append(p)
edits.append("features: GSUB_lookups.fea + GSUB.fea as one prefix")

# 6. kerning dropped: the shipped font has no GPOS
n = sum(len(right) for m in f.kerning.values() for right in m.values())
for mid in list(f.kerning.keys()):
    del f.kerning[mid]
edits.append("kerning removed (%d pairs): the shipped font has no GPOS" % n)

f.save(out)
for e in edits:
    print("-", e[:600])
