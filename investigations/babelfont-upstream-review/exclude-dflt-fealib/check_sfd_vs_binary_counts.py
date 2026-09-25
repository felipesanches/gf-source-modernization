"""Does a compiled font give every (table, script, language, feature) as many
lookups as the SFD registers for it? A count check, for binaries where lookup
names are gone (fea-rs output); fealib_langsys/check_sfd_vs_fealib compare names.

Usage: python check_sfd_vs_binary_counts.py FONT.sfd FEATURES.fea FONT.ttf
FEATURES.fea is the file the binary was built from; it tells which SFD lookups
the converter kept. aalt is skipped (no script/language statements allowed).
"""
import re, sys
from collections import defaultdict
from fontTools.ttLib import TTFont

sfd, fea_path, ttf = sys.argv[1:4]
fea = open(fea_path).read()
emitted = set(re.findall(r"^lookup (\w+) \{", fea, re.M))
san = lambda n: re.sub(r"[^0-9A-Za-z_]", "_", n)
expected = defaultdict(int)
for line in open(sfd, encoding="latin-1"):
    m = re.match(r'Lookup: (\d+) \d+ \d+ "([^"]*)"\s*\{.*?\}\s*\[(.*)\]\s*$', line)
    if not m or san(m.group(2)) not in emitted:
        continue
    table = "GPOS" if int(m.group(1)) >= 0x100 else "GSUB"
    for feat, body in re.findall(r"'(....)'\s*\(([^)]*)\)", m.group(3)):
        for script, langs in re.findall(r"'(....)'\s*<([^>]*)>", body):
            for lang in re.findall(r"'(....)'", langs):
                expected[(table, script.strip() or "DFLT", lang.strip() or "dflt", feat)] += 1
font = TTFont(ttf)
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
                got[(table, sr.ScriptTag, tag.strip(), fr.FeatureTag)] = len(fr.Feature.LookupListIndex)
bad = 0
for key in sorted(set(expected) | set(got)):
    if key[3] == "aalt":
        continue
    if expected.get(key, 0) != got.get(key, 0):
        bad += 1
        print(f"  {'/'.join(key)}: sfd {expected.get(key, 0)} binary {got.get(key, 0)}")
print("MISMATCHES", bad, "of", len(set(expected) | set(got)))
