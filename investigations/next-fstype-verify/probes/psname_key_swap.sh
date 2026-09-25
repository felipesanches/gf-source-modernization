#!/bin/bash
# psname_key_swap.sh -- is the Wallpoet PS-name loss only babelfont's choice of Glyphs key?
#
# Question answered: taking the .glyphs babelfont wrote for Wallpoet-Regular (run v2-fstype),
# renaming ONLY its font property key postscriptFullName -> postscriptFontName (what the
# proposed babelfont glyphs3 patch would write), and additionally (variant B) adding a
# font-level "Name Table Entry" custom parameter "4; Wallpoet", what name IDs 4 and 6 does
# gftools-builder3 e851b8b / fontc 1.0.0 build? Variant B tests the claim that no
# converter-side change can restore name ID 4.
# Run: bash psname_key_swap.sh    (writes runs/psname_key_swap.txt)
set -euo pipefail
S=/home/fsanches/compartilhado/sfd-reland-scratch/fstype-verify
V=/home/fsanches/compartilhado/sfd-reland/investigations/next-fstype-verify/runs
B3=/home/fsanches/compartilhado/builder3-worktrees/main-e851b8b/target/release/gftools-builder
PY=/home/fsanches/compartilhado/gftools/venv/bin/python3
SRC=$S/baseline/Wallpoet-Regular-fstype-verify-v2-fstype/sources/Wallpoet-Regular.glyphs
: > $V/psname_key_swap.txt
for variant in A B; do
  d=$S/psname-$variant; rm -rf $d; mkdir -p $d/sources
  sed 's/^key = postscriptFullName;$/key = postscriptFontName;/' $SRC > $d/sources/Wallpoet-Regular.glyphs
  if [ $variant = B ]; then
    "$PY" - $d/sources/Wallpoet-Regular.glyphs <<'PYEOF'
import sys, re
p = sys.argv[1]; t = open(p).read()
entry = '{\nname = "Name Table Entry";\nvalue = "4; Wallpoet";\n},\n'
if re.search(r'^customParameters = \(\n', t, re.M):
    t = re.sub(r'^customParameters = \(\n', lambda m: m.group(0) + entry, t, count=1, flags=re.M)
else:
    t = t.replace('.formatVersion = 3;\n', '.formatVersion = 3;\ncustomParameters = (\n' + entry + ');\n', 1)
open(p, 'w').write(t)
PYEOF
  fi
  printf 'buildVariable: false\nremoveOutlineOverlaps: false\nsources:\n  - Wallpoet-Regular.glyphs\n' > $d/sources/config.yaml
  (cd $d && "$B3" sources/config.yaml) > $d/build.log 2>&1
  "$PY" -c "
import glob; from fontTools.ttLib import TTFont
f = TTFont(glob.glob('$d/fonts/ttf/*.ttf')[0])
print('variant $variant:', {i: f['name'].getDebugName(i) for i in (1, 2, 4, 6)})" >> $V/psname_key_swap.txt
done
cat $V/psname_key_swap.txt
