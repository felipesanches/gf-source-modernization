"""Does a feature file emitted by babelfont's FontForge reader, compiled by
fontTools feaLib, give every GSUB/GPOS language system exactly the lookups the
SFD registers for it?

Usage: python check_sfd_vs_fealib.py FONT.sfd FEATURES.fea GLYPHORDER.txt
Ground truth: the SFD's `Lookup:` lines, ['feat' ('scrp' <'lang' ...> ...) ...].
Lookup names are sanitized the way babelfont does it (non-alphanumeric -> '_').
Prints one line per (table, script, language, feature) whose compiled lookup
list differs from the SFD registration, then a MISMATCHES count.
"""
import re, sys
from collections import defaultdict
import fontTools
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from io import StringIO
from fontTools.feaLib.builder import Builder

sfd, fea_path, order_path = sys.argv[1:4]
fea = open(fea_path).read()
order = [l.strip() for l in open(order_path) if l.strip()]
if ".notdef" not in order:
    order.insert(0, ".notdef")

san = lambda n: re.sub(r"[^0-9A-Za-z_]", "_", n)
expected = defaultdict(list)  # (table, script, lang, feat) -> [lookup names]
for line in open(sfd, encoding="latin-1"):
    m = re.match(r'Lookup: (\d+) \d+ \d+ "([^"]*)"\s*\{.*?\}\s*\[(.*)\]\s*$', line)
    if not m:
        continue
    table = "GPOS" if int(m.group(1)) >= 0x100 else "GSUB"
    name = san(m.group(2))
    for feat, body in re.findall(r"'(....)'\s*\(([^)]*)\)", m.group(3)):
        for script, langs in re.findall(r"'(....)'\s*<([^>]*)>", body):
            for lang in re.findall(r"'(....)'", langs):
                expected[(table, script.strip() or "DFLT", lang.strip() or "dflt", feat)].append(name)

fb = FontBuilder(1000, isTTF=True)
fb.setupGlyphOrder(order)
fb.setupGlyf({g: TTGlyphPen(None).glyph() for g in order})
fb.setupHorizontalMetrics({g: (500, 0) for g in order})
fb.setupHorizontalHeader(ascent=800, descent=-200)
font = fb.font
builder = Builder(font, StringIO(fea))
builder.build()
# Map each table's LookupList index back to its lookup-block name, the way
# feaLib numbers them (Builder.build_lookups_: lookups_ filtered by table).
by_obj = {id(b): n for n, b in builder.named_lookups_.items()}
defs = {t: [by_obj.get(id(l), "<anon>") for l in builder.lookups_ if l.table == t]
        for t in ("GSUB", "GPOS")}
emitted = set(builder.named_lookups_)

got = {}
for table in ("GSUB", "GPOS"):
    if table not in font:
        continue
    t = font[table].table
    for sr in t.ScriptList.ScriptRecord:
        systems = [("dflt", sr.Script.DefaultLangSys)] if sr.Script.DefaultLangSys else []
        systems += [(lr.LangSysTag, lr.LangSys) for lr in sr.Script.LangSysRecord]
        for tag, ls in systems:
            for fi in ls.FeatureIndex:
                fr = t.FeatureList.FeatureRecord[fi]
                got[(table, sr.ScriptTag, tag.strip(), fr.FeatureTag)] = [
                    defs[table][i] for i in fr.Feature.LookupListIndex]

print("fontTools", fontTools.version)
bad = 0
for key in sorted(set(expected) | set(got)):
    if key[3] == "aalt":
        continue  # aalt takes no script/language statements; separate issue
    want = sorted(n for n in expected.get(key, []) if n in emitted)
    have = sorted(got.get(key, []))
    if want != have:
        bad += 1
        miss = [n for n in want if n not in have]
        extra = [n for n in have if n not in want]
        print(f"  {'/'.join(key)}: missing {miss} extra {extra}")
print("MISMATCHES", bad, "of", len(set(expected) | set(got)))
