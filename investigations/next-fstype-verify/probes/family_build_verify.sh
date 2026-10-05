#!/bin/bash
# family_build_verify.sh -- titilliumweb from ONE config.yaml, the way tools/land.py builds it.
#
# Question answered: taking the .glyphs that baseline.sh left in scratch for runs
# <Style>=<run> (converter + workarounds already applied), and naming the built file as
# land.py's built_name() does (familyName + first instance name, spaces removed -- NOT
# the shipped file name), does every style build once and gate CLEAN in a family build?
#
# Usage: family_build_verify.sh <outdir> <Style>=<run> ...
set -uo pipefail
S=/home/fsanches/compartilhado/sfd-reland-scratch/fstype-verify
B3=/home/fsanches/compartilhado/builder3-worktrees/main-e851b8b/target/release/gftools-builder
D3=/home/fsanches/compartilhado/diffenator3-venv/bin/diffenator3
PY=/home/fsanches/compartilhado/gftools/venv/bin/python3
TG=/home/fsanches/compartilhado/sfd-batch5/tools/table_gate.py
FAM=/home/fsanches/compartilhado/gf-source-modernization/investigations/next-fstype-verify/runs/families-verify.tsv
out=$1; shift
d=$S/family-titilliumweb; rm -rf "$d"; mkdir -p "$d/sources" "$out"
printf 'buildVariable: false\nremoveOutlineOverlaps: false\nsources:\n' > "$d/sources/config.yaml"
for st in "$@"; do
  style=${st%%=*}; run=${st#*=}
  cp "$S/baseline/$style-fstype-verify-$run/sources/$style.glyphs" "$d/sources/" || exit 2
  echo "  - $style.glyphs" >> "$d/sources/config.yaml"
done
(cd "$d" && timeout 1800 "$B3" sources/config.yaml) > "$out/build.log" 2>&1 || { echo BUILD FAILED; exit 1; }
ls "$d/fonts/ttf" > "$out/built-files.txt"
: > "$out/summary.tsv"
for st in "$@"; do
  style=${st%%=*}
  name=$("$PY" -c "
import sys; sys.path.insert(0, '/home/fsanches/compartilhado/gf-source-modernization/tools')
import land; print(land.built_name('$d/sources/$style.glyphs'))")
  shipped=$(awk -F'\t' -v s="$style" 'NR>1 && $7==s {print $9}' "$FAM")
  built="$d/fonts/ttf/$name"
  [ -f "$built" ] || { printf '%s\tNOT-BUILT\t%s\n' "$style" "$name" >> "$out/summary.tsv"; continue; }
  "$D3" -J 1 --no-languages --no-match --json --succinct "$shipped" "$built" > "$d/$style.d3.json" 2>/dev/null
  "$PY" "$TG" "$d/$style.d3.json" --fonts "$shipped" "$built" > "$out/$style.gate.txt" 2>&1
  n=$(sed -n 's/^\([0-9]\{1,\}\) blocking table difference(s).*/\1/p' "$out/$style.gate.txt" | tail -1)
  printf '%s\t%s\t%s\n' "$style" "${n:-GATE-DID-NOT-FINISH}" "$name" >> "$out/summary.tsv"
done
cat "$out/summary.tsv"
