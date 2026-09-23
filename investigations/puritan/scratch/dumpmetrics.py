import sys
from fontTools.ttLib import TTFont
keys = ["head.unitsPerEm","head.xMin","head.yMin","head.xMax","head.yMax","head.fontRevision","hhea.ascent","hhea.descent","hhea.lineGap","OS/2.version","OS/2.usWeightClass","OS/2.fsType","OS/2.ySubscriptXSize","OS/2.ySubscriptYSize","OS/2.ySubscriptXOffset","OS/2.ySubscriptYOffset","OS/2.ySuperscriptXSize","OS/2.ySuperscriptYSize","OS/2.ySuperscriptXOffset","OS/2.ySuperscriptYOffset","OS/2.yStrikeoutSize","OS/2.yStrikeoutPosition","OS/2.sTypoAscender","OS/2.sTypoDescender","OS/2.sTypoLineGap","OS/2.usWinAscent","OS/2.usWinDescent","OS/2.sxHeight","OS/2.sCapHeight","OS/2.xAvgCharWidth","post.underlinePosition","post.underlineThickness","post.italicAngle"]
fonts=[TTFont(p) for p in sys.argv[1:]]
print("key\t"+"\t".join(p.split('/')[-2]+'/'+p.split('/')[-1] for p in sys.argv[1:]))
for k in keys:
    t,a=k.split('.')
    row=[]
    for f in fonts:
        try: row.append(str(getattr(f[t],a)))
        except Exception as e: row.append('-')
    print(k+"\t"+"\t".join(row))
for f,p in zip(fonts,sys.argv[1:]):
    print(p.split('/')[-1], sorted(f.keys()))
