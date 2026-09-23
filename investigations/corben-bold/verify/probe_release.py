# Independent re-read of every google/fonts version of Corben-Bold.ttf / Corben-Regular.ttf.
import sys
from fontTools.ttLib import TTFont
S=sys.argv[1]
E=2082844800
for sty in ("Bold","Regular"):
  for c in ["90abd17b4","bacec3651","5b1755d5a","ee1e172ab"]:
    try: f=TTFont("%s/rel/%s-%s.ttf"%(S,sty,c))
    except Exception as e: print(sty,c,"n/a"); continue
    o=f["OS/2"];h=f["hhea"];hd=f["head"];p=o.panose
    pv=[p.bFamilyType,p.bSerifStyle,p.bWeight,p.bProportion,p.bContrast,p.bStrokeVariation,p.bArmStyle,p.bLetterForm,p.bMidline,p.bXHeight]
    print(sty,c,"glyphs",len(f.getGlyphOrder()),"cmap",len(f.getBestCmap()),"created",hd.created-E,"rev",round(hd.fontRevision,4),
      "fsType",o.fsType,"wt",o.usWeightClass,"vend",repr(o.achVendID),"panose"," ".join(map(str,pv)),
      "typo",o.sTypoAscender,o.sTypoDescender,o.sTypoLineGap,"win",o.usWinAscent,o.usWinDescent,"hhea",h.ascent,h.descent,h.lineGap,
      "xh",o.sxHeight,"cap",o.sCapHeight,"fsSel",o.fsSelection,"mac",hd.macStyle)
