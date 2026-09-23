import sys
from fontTools.ttLib import TTFont
F = ["version","usWeightClass","ySubscriptXSize","ySubscriptYSize","ySubscriptYOffset","ySuperscriptXSize","ySuperscriptYSize","ySuperscriptYOffset","yStrikeoutSize","yStrikeoutPosition","achVendID","sTypoAscender","sTypoDescender","sTypoLineGap","usWinAscent","usWinDescent","sxHeight","sCapHeight","fsSelection"]
for p in sys.argv[1:]:
    f = TTFont(p); o = f["OS/2"]; h = f["hhea"]
    vals = {k: getattr(o, k, None) for k in F}
    pan = o.panose; pv = [pan.bFamilyType,pan.bSerifStyle,pan.bWeight,pan.bProportion,pan.bContrast,pan.bStrokeVariation,pan.bArmStyle,pan.bLetterForm,pan.bMidline,pan.bXHeight]
    print(p.split("/")[-2]+"/"+p.split("/")[-1], f["name"].getDebugName(5), "nglyphs", f["maxp"].numGlyphs)
    print("  OS/2", vals, "panose", pv)
    print("  hhea asc/desc/gap", h.ascent, h.descent, h.lineGap, "head yMin/yMax", f["head"].yMin, f["head"].yMax, "post ul", f["post"].underlinePosition, f["post"].underlineThickness)
