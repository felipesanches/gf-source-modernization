#!/usr/bin/env python3
"""Question answered: which fields of the shipped Corben-Bold.ttf were set by
FontForge from src/Corben-Bold.sfd, and which were edited later in google/fonts?

Reads every version of ofl/corben/Corben-Bold.ttf in the google/fonts history
(90abd17b4 initial 2015-03-07, bacec3651 fsType, 5b1755d5a "Update to correct internal
metadata" 2015-09-21, ee1e172ab ttfautohint 2017-08-29) and prints, per version:
head created/modified, the OS/2 + hhea fields in question, names 0-6, the RAW post
names of GIDs 211/548 (fontTools would rename the 2nd 'dcroat' to 'dcroat.1'), and the
STORED glyf header xMin vs hmtx lsb of AE/Lslash/lslash.
Usage: gftools/venv/bin/python3 release_history.py [google/fonts checkout]
"""
import struct
import subprocess
import sys
import io
from fontTools.ttLib import TTFont
from fontTools.ttLib.standardGlyphOrder import standardGlyphOrder

GF = sys.argv[1] if len(sys.argv) > 1 else "/home/fsanches/compartilhado/google/fonts"
MAC_EPOCH = 2082844800


def raw_post_names(f):
    raw = f.reader["post"]
    n, = struct.unpack(">H", raw[32:34])
    idx = struct.unpack(">%dH" % n, raw[34:34 + 2 * n])
    p, extra = 34 + 2 * n, []
    while p < len(raw):
        l = raw[p]
        extra.append(raw[p + 1:p + 1 + l].decode("latin1"))
        p += 1 + l
    return [standardGlyphOrder[i] if i < 258 else extra[i - 258] for i in idx]


for c in ["90abd17b4", "bacec3651", "5b1755d5a", "ee1e172ab"]:
    data = subprocess.run(["git", "-C", GF, "show", "%s:ofl/corben/Corben-Bold.ttf" % c],
                          capture_output=True, check=True).stdout
    f = TTFont(io.BytesIO(data))
    h, o, hh = f["head"], f["OS/2"], f["hhea"]
    names = {r.nameID: r.toUnicode() for r in f["name"].names if r.platformID == 3}
    pn = raw_post_names(f)
    print("== %s  %d bytes  glyphs %d  cmap %d" % (c, len(data), len(f.getGlyphOrder()), len(f.getBestCmap())))
    print("  head.created unix %d  modified unix %d" % (h.created - MAC_EPOCH, h.modified - MAC_EPOCH))
    print("  OS/2 typo %d/%d win %d/%d vendor %r panose.bSerifStyle %d weight %d xh %d cap %d"
          % (o.sTypoAscender, o.sTypoDescender, o.usWinAscent, o.usWinDescent, o.achVendID,
             o.panose.bSerifStyle, o.usWeightClass, o.sxHeight, o.sCapHeight))
    print("  hhea %d/%d" % (hh.ascent, hh.descent))
    for k in range(7):
        print("  name %d: %s" % (k, names.get(k)))
    print("  raw post name gid211=%s gid548=%s  duplicated raw names: %s"
          % (pn[211], pn[548], sorted({x for x in pn if pn.count(x) > 1})))
    glyf, loca, go = f.reader["glyf"], f["loca"], f.getGlyphOrder()
    out = []
    for g in ("AE", "Lslash", "lslash"):
        off = loca[go.index(g)]
        out.append("%s xMin %d lsb %d" % (g, struct.unpack(">h", glyf[off + 2:off + 4])[0], f["hmtx"][g][1]))
    print("  stored " + "; ".join(out))
