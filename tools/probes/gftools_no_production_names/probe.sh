#!/bin/sh
# Question answered: does Python gftools builder, patched to accept noProductionNames
# (gftools branch config-no-production-names), keep the source's glyph names, and does it
# rename them without the key?
# Builds one landed repo's style twice (config as landed; config minus the key) with the
# gftools in <venv>, then compares glyph orders with the .glyphs glyph names.
# Signal: "with: names not in source: 0" and "without: names not in source: N>0".
#   REPOS=<dir> sh probe.sh <scratch dir> <venv with patched gftools> [repo] [style]
set -eu
S=${1:?scratch}; V=${2:?venv}; R=${3:-quantico}; ST=${4:-Quantico-Regular}
REPOS=${REPOS:?set REPOS to the directory holding the landed repositories}
export PATH="$V/bin:$PATH"
for v in with without; do
  mkdir -p "$S/$v"; git -C "$REPOS/$R" archive HEAD sources | tar -x -C "$S/$v"
done
sed -i '/^noProductionNames: true$/d' "$S/without/sources/config.yaml"
for v in with without; do
  ( cd "$S/$v/sources" && gftools builder config.yaml --experimental-simple-output "$S/$v/out" \
      --experimental-single-source "$ST.glyphs" > "$S/$v/build.log" 2>&1 ) || echo "$v: build failed"
done
"$V/bin/python" - "$S" "$ST" <<'PY'
import re, sys
from fontTools.ttLib import TTFont
s, st = sys.argv[1], sys.argv[2]
src = set(re.findall(r'^glyphname = "?([^";]+)"?;', open(f"{s}/with/sources/{st}.glyphs").read(), re.M))
for v in ("with", "without"):
    names = TTFont(f"{s}/{v}/out/{st}.ttf").getGlyphOrder()
    print(f"{v}: {len(names)} glyphs, names not in source: {len(set(names) - src)}",
          sorted(set(names) - src)[:8])
PY
