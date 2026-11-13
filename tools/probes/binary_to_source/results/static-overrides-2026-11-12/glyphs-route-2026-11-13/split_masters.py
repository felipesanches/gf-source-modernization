#!/usr/bin/env python3
"""Question: can itfoundry/kumar's one Glyphs file (masters "Filled" and "Outlined", really two
families, no instances) be split into one single-master source per family that gftools builds?

Usage: split_masters.py "<Kumar One.glyphs>" <out dir>
Writes KumarOne.glyphs (master Filled) and KumarOneOutline.glyphs (master Outlined): the other
master and its layers are dropped, familyName set, nothing else touched.
"""
import os, sys
import glyphsLib

src, out = sys.argv[1:3]
os.makedirs(out, exist_ok=True)
for custom, family, stem in (("Filled", "Kumar One", "KumarOne"), ("Outlined", "Kumar One Outline", "KumarOneOutline")):
    f = glyphsLib.GSFont(src)
    keep = [m for m in f.masters if m.customName == custom or m.name == custom]
    assert len(keep) == 1, [(m.name, m.customName) for m in f.masters]
    mid = keep[0].id
    for g in f.glyphs:
        for layer in list(g.layers):
            if layer.associatedMasterId != mid:
                del g.layers[layer.layerId]
    f.masters = keep
    f.familyName = family
    f.save(os.path.join(out, stem + ".glyphs"))
    print(stem, len(f.glyphs), "glyphs")
