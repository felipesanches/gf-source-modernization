# Independent check: which tables differ (raw bytes) between release and each candidate.
import sys, glob
from fontTools.ttLib import TTFont
gf = "/home/fsanches/compartilhado/google/fonts/ofl/play"
V = sys.argv[1]
for s in ["Regular", "Bold"]:
    rel = TTFont(f"{gf}/Play-{s}.ttf")
    for c in ["3565c8a", "f17f03f", "0ae17b7", "7247d07"]:
        p = f"{V}/m4/{c}-Play-{s}.ttf"
        f = TTFont(p)
        tabs = sorted(set(rel.reader.keys()) | set(f.reader.keys()))
        diff = [t for t in tabs if t not in rel.reader or t not in f.reader or rel.reader[t] != f.reader[t]]
        extra = ""
        if "glyf" in diff and rel.getGlyphOrder() == f.getGlyphOrder():
            ga, gb = rel["glyf"], f["glyf"]
            n = 0
            for g in rel.getGlyphOrder():
                a = ga[g].getCoordinates(ga); b = gb[g].getCoordinates(gb)
                if list(a[0]) != list(b[0]) or list(a[1]) != list(b[1]) or list(a[2]) != list(b[2]):
                    n += 1
            extra = f" glyf coord/endpts/flags diffs={n}"
        print(s, c, "ver", f["name"].getDebugName(5), "| differing tables:", diff, extra, "| glyph order equal:", rel.getGlyphOrder() == f.getGlyphOrder())
    print(s, "release ver", rel["name"].getDebugName(5), "numGlyphs", rel["maxp"].numGlyphs)
