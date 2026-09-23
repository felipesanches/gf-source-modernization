#!/usr/bin/env python3
"""Question answered: which source file in librefonts/corben@94d5b00 has the glyph
set and cmap of the shipped Corben-Bold.ttf?

Compares the release (and the original 2015 google/fonts binary, 90abd17b4) with:
  src/Corben-Bold.sfd      (551 StartChar)
  src/Corben-Bold-TTF.sfd  (0 StartChar -- truncated)
  src/Corben-Bold.otf.*.ttx (a CFF build dumped to ttx; its cmap + GlyphOrder)
Usage: gftools/venv/bin/python3 cmap_provenance.py <tree> <release.ttf>
<tree> = `git -C <archive>/librefonts/corben.git archive 94d5b00e | tar -x -C <tree>`
"""
import re
import sys
from fontTools.ttLib import TTFont

tree, rel_path = sys.argv[1], sys.argv[2]
rel = TTFont(rel_path)
rcm = rel.getBestCmap()
rgo = rel.getGlyphOrder()


def sfd_glyphs(path):
    t = open(path, encoding="latin1").read()
    out = []  # (gid, name, unicode(s))
    for m in re.finditer(r"^StartChar: ([^\n]*)\nEncoding: (-?\d+) (-?\d+) (\d+)\n(.*?)^EndChar", t, re.M | re.S):
        cps = [int(m.group(3))] if int(m.group(3)) >= 0 else []
        for a in re.finditer(r"^AltUni2: (.*)$", m.group(5), re.M):
            cps += [int(x, 16) for x, _, _ in re.findall(r"([0-9a-f]+)\.([0-9a-f]+)\.([0-9a-f]+)", a.group(1))]
        out.append((int(m.group(4)), m.group(1), cps))
    return out


for src in ("src/Corben-Bold.sfd", "src/Corben-Bold-TTF.sfd"):
    g = sfd_glyphs("%s/%s" % (tree, src))
    cm = {u: n for _, n, us in g for u in us}
    names = [n for _, n, _ in g]
    dup = sorted({n for n in names if names.count(n) > 1})
    print("%-26s glyphs %3d  cmap %3d  duplicate names %s" % (src, len(g), len(cm), dup or "none"))
    if g:
        print("   release cmap - source cmap: %s" % sorted("%04X" % u for u in set(rcm) - set(cm)))
        print("   source cmap - release cmap: %s" % sorted("%04X" % u for u in set(cm) - set(rcm)))
        print("   codepoints mapped to a different glyph name: %s"
              % [("%04X" % u, cm[u], rcm[u]) for u in set(cm) & set(rcm) if cm[u] != rcm[u]])
        rel_names = set(rgo)
        print("   release glyphs not in source: %s" % sorted(rel_names - set(names)))
        print("   source glyphs not in release: %s" % sorted(set(names) - rel_names))

ot = open("%s/src/Corben-Bold.otf._c_m_a_p.ttx" % tree).read()
ocm = {int(c, 16) for c in re.findall(r'<map code="(0x[0-9a-f]+)"', ot)}
ogo = re.findall(r'<GlyphID id="\d+" name="([^"]+)"', open("%s/src/Corben-Bold.otf.GlyphOrder.ttx" % tree).read())
print("%-26s glyphs %3d  cmap %3d  (release cmap - otf cmap: %d codepoints)"
      % ("src/Corben-Bold.otf.ttx", len(ogo), len(ocm), len(set(rcm) - ocm)))
print("%-26s glyphs %3d  cmap %3d" % ("release", len(rgo), len(rcm)))
