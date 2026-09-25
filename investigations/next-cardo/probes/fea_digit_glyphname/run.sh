#!/bin/sh
# Build both repro sources (see make.py's docstring for the question).
# Usage: sh run.sh [scratch-dir]   (builds happen in a copy under scratch-dir)
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
PY=/home/fsanches/compartilhado/gftools/venv/bin/python3
B3=/home/fsanches/compartilhado/builder3-worktrees/main-e851b8b/target/release/gftools-builder
SCR=${1:-/home/fsanches/compartilhado/sfd-reland-scratch/cardo/fea-digit-repro}
"$PY" "$HERE/make.py"
for stem in DigitName LetterName; do
  rm -rf "$SCR/$stem"; mkdir -p "$SCR/$stem"; cp "$HERE/$stem/"* "$SCR/$stem/"
  if (cd "$SCR/$stem" && "$B3" --no-progress config.yaml >build.log 2>&1); then r=BUILT; else r="FAILED: $(grep -o "FEA parsing failed.*" "$SCR/$stem/build.log" | head -1)"; fi
  echo "fontc(builder3 e851b8b) $stem: $r"
  "$PY" - "$HERE/$stem/salt.fea" "$stem" <<'PYEOF'
import sys
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
from fontTools.fontBuilder import FontBuilder
name = "10192.04" if sys.argv[2] == "DigitName" else "u10192.04"
fb = FontBuilder(1000, isTTF=True); fb.setupGlyphOrder([".notdef", "a", name])
try:
    addOpenTypeFeaturesFromString(fb.font, open(sys.argv[1]).read())
    print("feaLib %s: BUILT" % sys.argv[2])
except Exception as e:
    print("feaLib %s: FAILED: %s" % (sys.argv[2], str(e).splitlines()[0][-90:]))
PYEOF
done
