"""Does workarounds.gdef_classes_fea restate exactly the GlyphClassDef the reverted reader commit
(47f99442) wrote? Compares the statement it adds to the one in <repo>.prev's source."""
import re, sys
sys.path.insert(0, "tools")
import workarounds
from fontTools.ttLib import TTFont
for fam, style, ttf in (("carlito", "Carlito-Regular", "Carlito-Regular.ttf"), ("sansation", "Sansation-Regular", "Sansation-Regular.ttf")):
    cur = open("/home/fsanches/compartilhado/sfd-reland-repos/%s/sources/%s.glyphs" % (fam, style), encoding="utf-8").read()
    prev = open("/home/fsanches/compartilhado/sfd-reland-repos/%s.prev/sources/%s.glyphs" % (fam, style), encoding="utf-8").read()
    assert "GlyphClassDef" not in cur
    new = workarounds.gdef_classes_fea(cur, TTFont(sys.argv[1] + "/" + ttf))
    a = re.search(r"GlyphClassDef (.*?);", new, re.S).group(1)
    b = re.search(r"GlyphClassDef (.*?);", prev, re.S).group(1)
    norm = lambda x: re.sub(r"\s+", " ", x).strip()
    print(fam, "SAME statement as the reverted reader wrote" if norm(a) == norm(b) else "DIFFERENT", len(norm(a)), len(norm(b)))
    if norm(a) != norm(b):
        import difflib
        for l in list(difflib.unified_diff(norm(b).split(" "), norm(a).split(" "), lineterm="", n=0))[:12]: print("  ", l[:100])
    print("  entry head:", new[new.index("featurePrefixes = (\n"):][:60].replace("\n", "|"))
