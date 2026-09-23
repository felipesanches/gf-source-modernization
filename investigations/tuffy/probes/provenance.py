"""Question: what toolchain built each Tuffy binary? Prints, per font, the
table set, FFTM timestamps, head created/modified, OS/2 version and the
sub/super/strike fields, fsType, name IDs 3/5 and glyph/cmap counts.
Usage: provenance.py <font.ttf|otf> ..."""
import sys, datetime
from fontTools.ttLib import TTFont
from fontTools.misc.timeTools import timestampToString
for p in sys.argv[1:]:
    f = TTFont(p)
    print("==", p)
    print("  tables:", " ".join(sorted(f.keys())))
    h = f["head"]
    print("  head.created:", timestampToString(h.created), " modified:", timestampToString(h.modified), " fontRevision:", round(h.fontRevision, 4), " unitsPerEm:", h.unitsPerEm)
    if "FFTM" in f:
        t = f["FFTM"]
        print("  FFTM version:", t.version, " FFTimeStamp:", timestampToString(t.FFTimeStamp), " sourceCreated:", timestampToString(t.sourceCreated), " sourceModified:", timestampToString(t.sourceModified))
    o = f["OS/2"]
    print("  OS/2.version:", o.version, " fsType:", o.fsType, " usWeightClass:", o.usWeightClass, " achVendID:", o.achVendID)
    print("  sub(xs,ys,xo,yo):", o.ySubscriptXSize, o.ySubscriptYSize, o.ySubscriptXOffset, o.ySubscriptYOffset,
          " sup:", o.ySuperscriptXSize, o.ySuperscriptYSize, o.ySuperscriptXOffset, o.ySuperscriptYOffset,
          " strike:", o.yStrikeoutSize, o.yStrikeoutPosition)
    if o.version >= 2:
        print("  sxHeight:", o.sxHeight, " sCapHeight:", o.sCapHeight, " usDefaultChar:", o.usDefaultChar, " usBreakChar:", o.usBreakChar, " usMaxContext:", o.usMaxContext)
    for nid in (3, 5):
        r = f["name"].getName(nid, 3, 1, 0x409) or f["name"].getName(nid, 1, 0, 0)
        print("  name%d:" % nid, r.toUnicode() if r else None)
    print("  glyphs:", len(f.getGlyphOrder()), " cmap:", len(f.getBestCmap() or {}), " post.format:", f["post"].formatType)
    if "gasp" in f: print("  gasp:", f["gasp"].gaspRange)
    if "fpgm" in f: print("  fpgm bytes:", len(f["fpgm"].program.getBytecode()))
    if "TTFA" in f: print("  TTFA:", f["TTFA"].data[:200])
