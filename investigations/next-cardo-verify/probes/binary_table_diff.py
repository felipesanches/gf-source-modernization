"""binary_table_diff.py -- which tables (raw bytes and decompiled content) differ between
two binaries of the same font, and which glyph advances / cmap mappings / head fields
changed?

Question: google/fonts d70318ab8 ("Updating ofl/cardo/*ttf with nbspace and fsType
fixes") replaced Cardo-Italic.ttf; what exactly did it change relative to 90abd17b4?
Used to check the cardo unit's claim that ONLY the nonbreakingspace advance changed
(550 -> 575), plus cmap packing and the head checksum.

Run: $PY binary_table_diff.py <old.ttf> <new.ttf>
"""
import sys
from fontTools.ttLib import TTFont

a, b = TTFont(sys.argv[1]), TTFont(sys.argv[2])
print("tables old", sorted(a.reader.keys()))
print("tables new", sorted(b.reader.keys()))
for t in sorted(set(a.reader.keys()) | set(b.reader.keys())):
    ra = a.reader[t] if t in a.reader else None
    rb = b.reader[t] if t in b.reader else None
    if ra != rb:
        print("RAW differs:", t, len(ra or b""), len(rb or b""))
# decompiled comparisons
ha, hb = a["hmtx"].metrics, b["hmtx"].metrics
print("advance/lsb changes:", [(g, ha[g], hb.get(g)) for g in ha if ha[g] != hb.get(g)])
ca, cb = a.getBestCmap(), b.getBestCmap()
print("best cmap equal:", ca == cb)
for sub in a["cmap"].tables:
    print("  old cmap subtable", sub.platformID, sub.platEncID, sub.format, len(sub.cmap))
for sub in b["cmap"].tables:
    print("  new cmap subtable", sub.platformID, sub.platEncID, sub.format, len(sub.cmap))
for t in ("head", "OS/2", "hhea", "post", "maxp"):
    da, db = vars(a[t]), vars(b[t])
    diffs = {k: (da.get(k), db.get(k)) for k in set(da) | set(db)
             if k not in ("tableTag",) and da.get(k) != db.get(k) and not k.startswith("_")}
    print(t, "field changes:", {k: v for k, v in diffs.items() if k not in ("mapping", "extraNames", "glyphOrder")})
print("fsType", a["OS/2"].fsType, b["OS/2"].fsType)
print("name records equal:", sorted((n.nameID, n.platformID, n.platEncID, n.langID, n.toUnicode()) for n in a["name"].names)
      == sorted((n.nameID, n.platformID, n.platEncID, n.langID, n.toUnicode()) for n in b["name"].names))
print("glyph order equal:", a.getGlyphOrder() == b.getGlyphOrder())
