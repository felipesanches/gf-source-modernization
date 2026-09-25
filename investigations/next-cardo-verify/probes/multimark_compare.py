"""multimark_compare.py -- do the release and a build shape MULTI-mark clusters alike?

Question: the cardo unit's shaping corpus (next-cardo/probes/shaping_compare.py) has an
EMPTY base+mark+mark corpus for every Cardo style (it only builds it for scripts with
<= 40 bases, and Cardo's Hebrew has more once presentation forms count), so its
"0 differences in every corpus" never exercised a stacked cluster -- exactly where GPOS
lookup ORDER (the p3 lookup-placement claim) matters. This shapes, with HarfBuzz, in
both fonts:
  heb3   Hebrew letter (U+05D0..U+05EA) + point (U+05B0..U+05BC, U+05C1, U+05C2, U+05C7)
         + cantillation (U+0591..U+05AF)
  heb4   Hebrew letter + dagesh U+05BC + point + cantillation
  hebsh  shin U+05E9 + shin/sin dot + point + cantillation
  lat3   Latin letter (a-z, A-Z) + two combining marks from U+0300..U+036F (ordered pairs
         of 24 common ones)
  grk3   Greek letter (U+03B1..U+03C9, U+0391..U+03A9) + two marks from U+0300..U+0345
and compares per string the glyph sequence with absolute positions (glyph@x,y).
Only strings whose every codepoint both fonts map are shaped.

Run: $PY multimark_compare.py <release.ttf> <built.ttf> [--show N]
"""
import itertools
import sys

import uharfbuzz as hb
from fontTools.ttLib import TTFont


class Shaper:
    def __init__(self, path):
        self.font = hb.Font(hb.Face(hb.Blob.from_file_path(path)))
        tt = TTFont(path)
        self.order = tt.getGlyphOrder()
        self.cmap = tt.getBestCmap()
        rev = {}
        for cp, n in self.cmap.items():
            rev.setdefault(n, cp)
        self.key = lambda gid: ("U+%04X" % rev[self.order[gid]]) if self.order[gid] in rev \
            else self.order[gid]

    def run(self, text):
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        hb.shape(self.font, buf, {})
        out, x = [], 0
        for i, p in zip(buf.glyph_infos, buf.glyph_positions):
            out.append((self.key(i.codepoint), x + p.x_offset, p.y_offset))
            x += p.x_advance
        out.append(("END", x, 0))
        return out


def main():
    argv = sys.argv[1:]
    show = 5
    if "--show" in argv:
        i = argv.index("--show"); show = int(argv[i + 1]); del argv[i:i + 2]
    S, B = Shaper(argv[0]), Shaper(argv[1])
    shared = set(S.cmap) & set(B.cmap)
    letters = list(range(0x05D0, 0x05EB))
    points = list(range(0x05B0, 0x05BD)) + [0x05C1, 0x05C2, 0x05C7]
    cant = list(range(0x0591, 0x05B0))
    latm = [0x300, 0x301, 0x302, 0x303, 0x304, 0x306, 0x307, 0x308, 0x309, 0x30A, 0x30B,
            0x30C, 0x30F, 0x311, 0x312, 0x313, 0x314, 0x31B, 0x323, 0x324, 0x325, 0x326,
            0x327, 0x328]
    grkm = [0x300, 0x301, 0x304, 0x306, 0x308, 0x313, 0x314, 0x342, 0x343, 0x344, 0x345]
    corp = {
        "heb3": [(b, p, c) for b in letters for p in points for c in cant],
        "heb4": [(b, 0x05BC, p, c) for b in letters for p in points if p != 0x05BC for c in cant],
        "hebsh": [(0x05E9, d, p, c) for d in (0x05C1, 0x05C2) for p in points
                  if p not in (0x05C1, 0x05C2) for c in cant],
        "lat3": [(b, m1, m2) for b in list(range(0x61, 0x7B)) + list(range(0x41, 0x5B))
                 for m1, m2 in itertools.permutations(latm, 2)],
        "grk3": [(b, m1, m2) for b in list(range(0x3B1, 0x3CA)) + list(range(0x391, 0x3AA))
                 for m1, m2 in itertools.permutations(grkm, 2)],
    }
    for name, seqs in corp.items():
        seqs = [s for s in seqs if all(c in shared for c in s)]
        diffs = []
        for s in seqs:
            t = "".join(map(chr, s))
            a, b = S.run(t), B.run(t)
            if a != b:
                diffs.append((s, a, b))
        print("%-6s %6d strings %6d differ" % (name, len(seqs), len(diffs)))
        for s, a, b in diffs[:show]:
            print("   ", " ".join("U+%04X" % c for c in s))
            print("      release", " ".join("%s@%d,%d" % r for r in a))
            print("      ours   ", " ".join("%s@%d,%d" % r for r in b))


if __name__ == "__main__":
    main()
