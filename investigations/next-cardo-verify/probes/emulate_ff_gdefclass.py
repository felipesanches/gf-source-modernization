"""emulate_ff_gdefclass.py -- EMULATION of a converter rule on a converted .glyphs: give
every glyph that FontForge's gdefclass() exported as a BASE (no GlyphClass in the .sfd,
no mark/basemark anchor, no Ligature2 PST) an explicit `category = Letter;`, so that
fontc's GlyphData lookup cannot turn it into a mark.

Question: Cardo-Bold's release (FontForge 20110222) classes every glyph as a base; our
build classes 165 combining marks as marks because babelfont leaves zero-advance
glyphs uncategorised and fontc's GlyphData then makes them marks. Built for real with
builder3 e851b8b / fontc 1.0.0, does a source that states FontForge's classes close the
kern-across-mark difference (the cardo unit's 177/426) WITHOUT any fontc change, and
what do the gates say?

Run: $PY emulate_ff_gdefclass.py <in.glyphs> <source.sfd> <out.glyphs>
Only glyphs with no `category =` key are touched; the file text is edited in place of
re-serialising (see next-cardo/probes/mark_lookups_after_marker.py for why).
"""
import re
import sys

src, sfd, dst = sys.argv[1:4]
text = open(src, encoding="utf-8").read()
sfdtext = open(sfd, encoding="latin-1").read()
ff_base = set()
for m in re.finditer(r"^StartChar: (\S+)\n(.*?)^EndChar", sfdtext, re.M | re.S):
    name, body = m.group(1), m.group(2)
    gc = re.search(r"^GlyphClass: (\d+)", body, re.M)
    if gc:
        if int(gc.group(1)) == 2:
            ff_base.add(name)
        continue
    if re.search(r'^AnchorPoint: "[^"]*" \S+ \S+ (mark|basemark)', body, re.M):
        continue
    if re.search(r"^Ligature2:", body, re.M) or name == ".notdef":
        continue
    ff_base.add(name)
n = 0
out = []
pos = 0
# a glyph entry starts at "{\n" followed (after optional keys) by glyphname = X;
for m in re.finditer(r'\{\n((?:[a-zA-Z]+ = [^\n]*;\n)*?)glyphname = "?([^";\n]+)"?;\n', text):
    name = m.group(2)
    head = m.group(1)
    if name in ff_base and "category = " not in head:
        # is there a category key later in this glyph entry (before "layers")?
        tail = text[m.end():m.end() + 200]
        if re.match(r"(?:[a-zA-Z]+ = [^\n]*;\n)*?category = ", tail):
            continue
        out.append(text[pos:m.end()])
        out.append("category = Letter;\n")
        pos = m.end()
        n += 1
out.append(text[pos:])
open(dst, "w", encoding="utf-8").write("".join(out))
print("category = Letter added to %d glyph(s) FontForge exported as base" % n)
