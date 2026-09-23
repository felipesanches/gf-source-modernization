#!/bin/bash
# Question answered: can the converted .glyphs make fontc emit a GPOS that has scripts
# but no features/lookups (what FontForge's exporter wrote), just by adding an EMPTY
# GPOS feature block to the feature code? Adds `feature kern {} kern;` (a .glyphs
# features entry with tag kern and empty code) to the baseline conversion, builds it
# with the pinned gftools-builder3 (fontc 1.0.0), and prints whether a GPOS exists.
# Pass: "GPOS present" would mean the converter alone could close the rows.
#
#   bash fea_empty_feature_test.sh <baseline .glyphs> <workdir>
set -euo pipefail
G=$1; W=$2
B3=/home/fsanches/compartilhado/builder3-worktrees/main-e851b8b/target/release/gftools-builder
PY=/home/fsanches/compartilhado/gftools/venv/bin/python3
rm -rf "$W"; mkdir -p "$W/sources"
printf 'buildVariable: false\nremoveOutlineOverlaps: false\nsources:\n  - %s\n' "$(basename "$G")" > "$W/sources/config.yaml"
"$PY" - "$G" "$W/sources/$(basename "$G")" <<'PYEOF'
import sys
s = open(sys.argv[1]).read()
assert 'features = (\n{' in s
s = s.replace('features = (\n{', 'features = (\n{\ncode = "";\ntag = kern;\n},\n{', 1)
open(sys.argv[2], 'w').write(s)
PYEOF
(cd "$W" && timeout 900 "$B3" sources/config.yaml > build.log 2>&1)
"$PY" - "$W"/fonts/ttf/*.ttf <<'PYEOF'
import sys
from fontTools.ttLib import TTFont
f = TTFont(sys.argv[1])
if 'GPOS' in f:
    t = f['GPOS'].table
    print('GPOS present: scripts %s features %d lookups %d' % (
        [s.ScriptTag for s in t.ScriptList.ScriptRecord], t.FeatureList.FeatureCount,
        t.LookupList.LookupCount))
else:
    print('no GPOS table: an empty feature block does not make fontc emit one')
PYEOF
