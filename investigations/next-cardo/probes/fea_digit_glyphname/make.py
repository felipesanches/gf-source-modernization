#!/usr/bin/env python3
"""Minimal repro: a glyph whose name starts with a digit cannot be referenced from FEA.

Question answered: is Cardo-Regular's build failure ("FEA parsing failed with 2
errors") a fontc/fea-rs bug, or FEA itself? Writes two 3-glyph Glyphs 3 sources that
differ only in one glyph name -- DigitName.glyphs names it `10192.04` (as
Cardo-Regular-TTF.sfd does, gid 3416, U+F438), LetterName.glyphs `u10192.04` -- each
with a `salt` feature `sub a from [a <name>];`, as babelfont writes Cardo's
AlternateSubs2. run.sh compiles both with gftools-builder3 e851b8b (fontc 1.0.0) and
the FEA alone with fontTools feaLib.

Expected (EXPECTED.txt): DigitName fails in both compilers, LetterName builds. The
OpenType Feature File spec (2.f.i) says a glyph name "must not start with a digit";
so the defect is the source name, and the converter emitted FEA it could not express.
"""
import os
HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = '''{
.formatVersion = 3;
familyName = Repro;
fontMaster = (
{
id = m01;
name = Regular;
}
);
features = (
{
code = "sub a from [a %(name)s];";
tag = salt;
}
);
glyphs = (
{
glyphname = .notdef;
layers = (
{
layerId = m01;
width = 500;
}
);
},
{
glyphname = a;
layers = (
{
layerId = m01;
shapes = (
{
closed = 1;
nodes = (
(0,0,l),
(400,0,l),
(400,400,l)
);
}
);
width = 500;
}
);
unicode = 97;
},
{
glyphname = "%(name)s";
layers = (
{
layerId = m01;
shapes = (
{
closed = 1;
nodes = (
(0,0,l),
(300,0,l),
(300,300,l)
);
}
);
width = 500;
}
);
unicode = 62520;
}
);
unitsPerEm = 1000;
versionMajor = 1;
versionMinor = 0;
}
'''
for stem, name in (("DigitName", "10192.04"), ("LetterName", "u10192.04")):
    os.makedirs(os.path.join(HERE, stem), exist_ok=True)
    with open(os.path.join(HERE, stem, "Repro.glyphs"), "w") as fh:
        fh.write(TEMPLATE % {"name": name})
    with open(os.path.join(HERE, stem, "config.yaml"), "w") as fh:
        fh.write("buildVariable: false\nsources:\n  - Repro.glyphs\n")
    with open(os.path.join(HERE, stem, "salt.fea"), "w") as fh:
        fh.write("feature salt { sub a from [a %s]; } salt;\n" % name)
