"""Compile a feature file with fontTools feaLib and print, per (script, language),
the lookups of each feature, named by their lookup-block name.

Usage: python fealib_langsys.py FILE.fea
Glyphs: .notdef f i f_i f_f (the babelfont unit-test SFD's glyph set).
"""
import sys, re
import fontTools
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString

fea = open(sys.argv[1]).read()
order = [".notdef", "f", "i", "f_i", "f_f"]
fb = FontBuilder(1000, isTTF=True)
fb.setupGlyphOrder(order)
fb.setupCharacterMap({0x66: "f", 0x69: "i"})
fb.setupGlyf({g: TTGlyphPen(None).glyph() for g in order})
fb.setupHorizontalMetrics({g: (500, 0) for g in order})
fb.setupHorizontalHeader(ascent=800, descent=-200)
font = fb.font
addOpenTypeFeaturesFromString(font, fea)
names = re.findall(r"^\s*lookup\s+(\w+)\s*\{", fea, re.M)
gsub = font["GSUB"].table
print("fontTools", fontTools.version)
for sr in gsub.ScriptList.ScriptRecord:
    systems = []
    if sr.Script.DefaultLangSys:
        systems.append(("dflt", sr.Script.DefaultLangSys))
    systems += [(lr.LangSysTag, lr.LangSys) for lr in sr.Script.LangSysRecord]
    for tag, ls in systems:
        for fi in ls.FeatureIndex:
            fr = gsub.FeatureList.FeatureRecord[fi]
            lk = [names[i] for i in fr.Feature.LookupListIndex]
            print(f"  {sr.ScriptTag}/{tag.strip()} {fr.FeatureTag}: {lk}")
