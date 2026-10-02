"""Question: for each of the 10 Play residual items, what do the release, fontmake/glyphsLib
and a gftools-builder build produce?  Usage: items.py <style> <label=ttf> ..."""
import sys
from fontTools.ttLib import TTFont
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import RecordingPen
def item(f):
    o = {}
    gs = f.getGlyphSet(); cmap = f.getBestCmap()
    gsub = f["GSUB"].table
    scripts = {sr.ScriptTag: [gsub.FeatureList.FeatureRecord[i].FeatureTag for i in sr.Script.DefaultLangSys.FeatureIndex] for sr in gsub.ScriptList.ScriptRecord}
    o["1 GSUB latn features"] = sorted(set(scripts.get("latn", [])))
    o["1 GSUB scripts"] = sorted(scripts)
    a = cmap.get(0x301)
    bp = BoundsPen(gs); gs[a].draw(bp)
    o["2 acutecomb name/adv/xbounds"] = (a, f["hmtx"][a][0], bp.bounds and (bp.bounds[0], bp.bounds[2]))
    o["3 names U+0122 U+0306 U+000D"] = (cmap.get(0x122), cmap.get(0x306), cmap.get(0xD), "brevecombcy" in gs, "uni0306.cy" in gs)
    o["4 FB00 FB03 FB04"] = [cmap.get(c) for c in (0xFB00, 0xFB03, 0xFB04)] + ["ff" in gs and "ff", "f_f" in gs and "f_f"]
    o["5 usWeightClass, ID4, ID6"] = (f["OS/2"].usWeightClass, f["name"].getDebugName(4), f["name"].getDebugName(6), f["OS/2"].fsSelection, f["head"].macStyle)
    o["6 panose weight"] = f["OS/2"].panose.bWeight
    o["7 underline pos/thick"] = (f["post"].underlinePosition, f["post"].underlineThickness)
    gdef = f["GDEF"].table
    o["8 GDEF version, markattach, marksets"] = (hex(gdef.Version), bool(gdef.MarkAttachClassDef), bool(getattr(gdef, "MarkGlyphSetsDef", None)))
    g = cmap.get(0x122); 
    if "glyf" in f:
        gl = f["glyf"][g]; 
        o["9 U+0122 points/components"] = (gl.getCoordinates(f["glyf"])[0].__len__(), gl.isComposite())
    o["10 hinted (fpgm)"] = "fpgm" in f
    return o
res = {}
for a in sys.argv[1:]:
    lab, p = a.split("=", 1); res[lab] = item(TTFont(p))
keys = list(next(iter(res.values())))
for k in keys:
    print(k)
    for lab in res: print("   %-10s %s" % (lab, res[lab].get(k)))
