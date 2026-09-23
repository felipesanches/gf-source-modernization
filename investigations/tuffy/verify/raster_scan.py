#!/usr/bin/env python3
"""Adversarial verification, unit "tuffy".

Question it answers: independent of table_gate.py's measures (advance, bbox within
2 units, per-contour |area| within 0.4%), which codepoints RENDER differently in
two fonts? Each glyph is rasterised by FreeType, unhinted, 1-bit, nonzero fill,
at --ppem pixels per em (default 1024 = 0.5 px per unit at 2048 upm), in one
shared pixel frame (origin at the pen position), and the differing pixels are
counted. ratio = differing pixels / max(filled pixels of either).

Usage: raster_scan.py <release.ttf> <built.ttf> [--min 0.01] [--ppem 1024]
       [--cps U+XXXX,...]
Prints one line per codepoint whose advance differs or whose ratio >= --min,
sorted by ratio, then "N codepoint(s) compared, M differ".
"""
import sys
import freetype
from fontTools.ttLib import TTFont

FLAGS = freetype.FT_LOAD_NO_HINTING | freetype.FT_LOAD_NO_BITMAP | freetype.FT_LOAD_TARGET_MONO


def rows(face, gid):
    """{y: int bitmask of filled x (bit x+OFF)} for one glyph."""
    face.load_glyph(gid, FLAGS)
    face.glyph.render(freetype.FT_RENDER_MODE_MONO)
    bm = face.glyph.bitmap
    left, top = face.glyph.bitmap_left, face.glyph.bitmap_top
    buf = bm.buffer
    out = {}
    OFF = 1 << 14
    for r in range(bm.rows):
        chunk = bytes(buf[r * bm.pitch:(r + 1) * bm.pitch])
        v = int.from_bytes(chunk, "big")
        if not v:
            continue
        # MSB of the row is pixel 0; normalise so bit i = pixel (left + i)
        nbits = bm.pitch * 8
        v = int(bin(v)[2:].zfill(nbits)[::-1], 2)
        out[top - r] = v << (left + OFF)
    return out


def popcount(v):
    return bin(v).count("1")


def main():
    a, b = sys.argv[1], sys.argv[2]
    mn, ppem, cps = 0.01, 1024, None
    if "--min" in sys.argv:
        mn = float(sys.argv[sys.argv.index("--min") + 1])
    if "--ppem" in sys.argv:
        ppem = int(sys.argv[sys.argv.index("--ppem") + 1])
    if "--cps" in sys.argv:
        cps = [int(x[2:], 16) for x in sys.argv[sys.argv.index("--cps") + 1].split(",")]
    ta, tb = TTFont(a), TTFont(b)
    ca, cb = ta.getBestCmap(), tb.getBestCmap()
    fa, fb = freetype.Face(a), freetype.Face(b)
    for f in (fa, fb):
        f.set_char_size(ppem * 64, 0, 72, 72)
    shared = sorted(set(ca) & set(cb)) if cps is None else cps
    out = []
    for cp in shared:
        na, nb = ca[cp], cb[cp]
        adva, advb = ta["hmtx"][na][0], tb["hmtx"][nb][0]
        ra = rows(fa, ta.getGlyphID(na))
        rb = rows(fb, tb.getGlyphID(nb))
        pa = sum(popcount(v) for v in ra.values())
        pb = sum(popcount(v) for v in rb.values())
        d = sum(popcount(ra.get(y, 0) ^ rb.get(y, 0)) for y in set(ra) | set(rb))
        ratio = d / max(pa, pb, 1)
        if adva != advb or ratio >= mn:
            out.append((ratio, cp, na, nb, adva, advb, pa, pb, d))
    for ratio, cp, na, nb, adva, advb, pa, pb, d in sorted(out, reverse=True):
        print("U+%04X %-24s %-28s adv %5d %5d  px %7d %7d  diff %6d  ratio %.4f"
              % (cp, na, nb, adva, advb, pa, pb, d, ratio))
    print("%d codepoint(s) compared, %d differ (advance, or >= %.3f of pixels at %d ppem)"
          % (len(shared), len(out), mn, ppem))


if __name__ == "__main__":
    main()
