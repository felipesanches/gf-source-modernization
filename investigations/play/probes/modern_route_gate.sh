#!/bin/bash
# Question answered: how far is today's pinned toolchain from reproducing the Play
# release out of its REAL source, m4rc1e/play sources/Play.glyphs (Glyphs 2,
# appVersion 983), and which converter defects stand in the way?
#
# 1. babelfont (gf-sfd-conversion f725e6a) reads Play.glyphs and writes Glyphs 3;
#    prints what it made of `unicode = 2013;` (endash; Glyphs 2 unicodes are hex)
#    and of the Bold instance's location (Glyphs 2 default interpolationWeight 100).
# 2. gftools-builder3 e851b8b (fontc 1.0.0), buildVariable: false.
# 3. diffenator3 + sfd-batch5/tools/table_gate.py against the release, per style
#    that was built.
#
# Usage: probes/modern_route_gate.sh [mirror] [outdir]
set -uo pipefail
M=${1:-/home/fsanches/compartilhado/upstream_repos/repo_archive/m4rc1e/play.git}
OUT=${2:-$(cd "$(dirname "$0")/.." && pwd)/runs/modern}
BF=/home/fsanches/compartilhado/babelfont-rs-worktrees/gf-sfd-conversion/target/release/babelfont
B3=/home/fsanches/compartilhado/builder3-worktrees/main-e851b8b/target/release/gftools-builder
D3=/home/fsanches/compartilhado/diffenator3-venv/bin/diffenator3
PY=/home/fsanches/compartilhado/gftools/venv/bin/python3
TG=/home/fsanches/compartilhado/sfd-batch5/tools/table_gate.py
GF=/home/fsanches/compartilhado/google/fonts
mkdir -p "$OUT"; w=$(mktemp -d); mkdir -p "$w/sources"
git -C "$M" show 3565c8a:sources/Play.glyphs > "$w/sources/Play.glyphs"
"$BF" "$w/sources/Play.glyphs" "$w/rt.glyphs" > /dev/null 2>&1
{ echo "source: endash $(awk '$0=="glyphname = endash;"{p=1;next} p&&/^glyphname = /{exit} p&&/^unicode = /{print;exit}' "$w/sources/Play.glyphs") (Glyphs 2: hex)"
  echo "babelfont G3 out: endash $(awk '$0=="glyphname = endash;"{p=1;next} p&&/^glyphname = /{exit} p&&/^unicode = /{print;exit}' "$w/rt.glyphs") (Glyphs 3: decimal; 8211 expected)"
  echo "babelfont G3 out: instances:"; awk '/^instances = \(/{p=1} p&&/^(axesValues|name) = /{print "  "$0} p&&/^\);/{exit}' "$w/rt.glyphs"
} | tee "$OUT/babelfont_glyphs2_read.txt"
printf 'buildVariable: false\nsources:\n  - Play.glyphs\n' > "$w/sources/config.yaml"
(cd "$w" && "$B3" --generate sources/config.yaml) > "$OUT/recipe.yaml" 2>&1
(cd "$w" && timeout 1500 "$B3" sources/config.yaml) > "$OUT/build.log" 2>&1; echo "builder3 rc=$?" | tee -a "$OUT/build.log"
for s in Regular Bold; do
  b="$w/fonts/ttf/Play-$s.ttf"
  if [ ! -s "$b" ]; then echo "Play-$s: NOT BUILT" | tee "$OUT/Play-$s.gate.txt"; continue; fi
  "$D3" -J 1 --no-languages --no-match --json --succinct "$GF/ofl/play/Play-$s.ttf" "$b" > "$w/d3.json" 2>/dev/null
  "$PY" "$TG" "$w/d3.json" --fonts "$GF/ofl/play/Play-$s.ttf" "$b" > "$OUT/Play-$s.gate.txt" 2>&1
  echo "Play-$s: $(tail -1 "$OUT/Play-$s.gate.txt")"
done
rm -rf "$w"
