#!/usr/bin/env python3
"""Question answered: had FontForge exported a TTF from a font it loaded from a
CFF-flavoured OpenType (.otf) -- cubic outlines, the CFF Private dict as the PS
private dict -- which OS/2 sxHeight/sCapHeight would its exporter have written?

FontForge measures the outlines IN MEMORY (the cubic splines it read), not the
quadratic ones it writes to glyf. This feeds a .otf's charstrings, as FontForge's
PostScript reader builds them (closepath adds a closing line unless the last point
is the first), to the rule implemented in ff_heights_probe.py.

Usage: <venv python3> cff_heights_probe.py <file.otf> [2011|2012] [dump]
"""
import sys

from fontTools.pens.basePen import BasePen
from fontTools.ttLib import TTFont

sys.path.insert(0, __file__.rsplit("/", 1)[0])
import ff_heights_probe as P  # noqa: E402


class Rec(BasePen):
    def __init__(self, gs):
        super().__init__(gs)
        self.contours = []

    def _moveTo(self, p):
        self.contours.append([("m", tuple(map(float, p)))])

    def _lineTo(self, p):
        self.contours[-1].append(("l", tuple(map(float, p))))

    def _curveToOne(self, a, b, c):
        self.contours[-1].append(("c", tuple(map(float, a)), tuple(map(float, b)),
                                  tuple(map(float, c))))

    def _closePath(self):
        con = self.contours[-1]
        first = con[0][1]
        last = con[-1][-1]
        if last != first:
            con.append(("l", first))

    _endPath = _closePath


def load(path):
    f = TTFont(path)
    gs = f.getGlyphSet()
    order = f.getGlyphOrder()
    cmap = f.getBestCmap()
    unis = {}
    for u, n in cmap.items():
        unis.setdefault(n, []).append(u)
    font = {"ascent": 0.0, "descent": 0.0, "order2": False, "blues": None, "glyphs": {}}
    upm = f["head"].unitsPerEm
    # FontForge's CFF import: ascent/descent from hhea/OS2 scaled to the em; only
    # their sum (the em) matters to the BlueValues tolerance.
    font["ascent"], font["descent"] = 0.8 * upm, 0.2 * upm
    if "CFF " in f:
        pr = f["CFF "].cff.topDictIndex[0].Private
        bv = getattr(pr, "BlueValues", None)
        if bv:
            font["blues"] = "[" + " ".join(str(v) for v in bv) + "]"
    for gid, n in enumerate(order):
        pen = Rec(gs)
        gs[n].draw(pen)
        font["glyphs"][gid] = {"name": n, "unis": unis.get(n, []), "gid": gid,
                               "contours": pen.contours, "refs": []}
    return font


def main():
    path = sys.argv[1]
    year = int(sys.argv[2]) if len(sys.argv) > 2 else 2012
    v = P.V(year)
    font = load(path)
    print("%s vintage=%d blues=%s" % (path, year, font["blues"]))
    for name, lst in (("x-height", P.XH), ("cap height", P.CAP)):
        tr = []
        res, flats, curves = P.standard_height(v, font, lst, tr)
        if len(sys.argv) > 3:
            for ch, gname, t, f in tr:
                print("  U+%04X %-14s %-8s %.6f" % (ch, gname, f, t))
        print("%-10s flats=%s curves=%s" % (name, [(round(p, 4), c) for p, c in flats],
                                             [(round(p, 4), c) for p, c in curves]))
        print("%-10s raw %s -> exported %d" % (name, None if res is None else round(res[0], 6),
                                                P.exported(res)))


if __name__ == "__main__":
    main()
