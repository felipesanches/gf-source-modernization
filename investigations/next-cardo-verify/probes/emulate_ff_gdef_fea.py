"""emulate_ff_gdef_fea.py -- EMULATION of a converter rule on a converted .glyphs: state
FontForge's own GDEF glyph classes (tottfgpos.c gdefclass(): the .sfd's GlyphClass, else
mark for a mark/basemark anchor, else ligature for a Ligature2 PST, else base; .notdef
unclassed) as an explicit FEA `table GDEF { GlyphClassDef ... } GDEF;` featurePrefix.

Question: a Glyphs category cannot make fontc list BASE glyphs in GDEF when a font has no
anchors -- setting category = Letter on Cardo-Bold's combining marks made fontc omit GDEF
altogether, and HarfBuzz then synthesised mark classes from Unicode
(runs/emu-bold-ffgdef). Does stating FontForge's classes in the feature file, built for
real with builder3 e851b8b / fontc 1.0.0, give the release's GDEF -- and with it the
release's kern-across-mark behaviour -- WITHOUT the fontc ignoreMarks=false change the
cardo unit proposes?

Run: $PY emulate_ff_gdef_fea.py <in.glyphs> <source.sfd> <out.glyphs>
"""
import re
import sys

src, sfd, dst = sys.argv[1:4]
text = open(src, encoding="utf-8").read()
s = open(sfd, encoding="latin-1").read()
cls = {1: [], 2: [], 3: [], 4: []}
for m in re.finditer(r"^StartChar: (\S+)\n(.*?)^EndChar", s, re.M | re.S):
    name, body = m.group(1), m.group(2)
    gc = re.search(r"^GlyphClass: (\d+)", body, re.M)
    if gc:
        c = int(gc.group(1)) - 1
    elif name == ".notdef":
        c = 0
    elif re.search(r'^AnchorPoint: "[^"]*" \S+ \S+ (mark|basemark)', body, re.M):
        c = 3
    elif re.search(r"^Ligature2:", body, re.M):
        c = 2
    else:
        c = 1
    if c in cls:
        cls[c].append(name)
glyphs_in = set(re.findall(r'^glyphname = "?([^";\n]+)"?;', text, re.M))
def fmt(names):
    # a name FEA cannot express (leading digit or a character outside A-Za-z0-9._-, e.g.
    # Cardo-Italic 1E0A and uniA78#) is left unclassed
    names = [n for n in names if n in glyphs_in and re.fullmatch(r"[A-Za-z_.][A-Za-z0-9_.\-]*", n)]
    return "[" + " ".join(names) + "]" if names else ""
fea = "table GDEF {\\n    GlyphClassDef %s, %s, %s, %s;\\n} GDEF;" % (
    fmt(cls[1]), fmt(cls[2]), fmt(cls[3]), fmt(cls[4]))
entry = '{\ncode = "%s";\nname = FontForgeGlyphClassDef;\n},\n' % fea.replace("\\n", "\n")
assert text.count("featurePrefixes = (\n") == 1
text = text.replace("featurePrefixes = (\n", "featurePrefixes = (\n" + entry, 1)
open(dst, "w", encoding="utf-8").write(text)
print("GlyphClassDef base %d, ligature %d, mark %d, component %d" %
      tuple(len([n for n in cls[k] if n in glyphs_in]) for k in (1, 2, 3, 4)))
