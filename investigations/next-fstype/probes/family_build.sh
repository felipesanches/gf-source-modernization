#!/bin/bash
# family_build.sh -- the whole family from ONE config.yaml, as tools/land.py builds it.
#
# Question answered: tools/baseline.sh builds each style alone; land.py writes one
# config.yaml naming every style's .glyphs and builds them together. With the
# candidate sources of a harness run (the .glyphs baseline.sh left in scratch, after
# bf_with_workarounds.sh), does the one-config build produce exactly one font per
# shipped file name, and does each gate as it did alone (same verdict, same rows)?
#
# Usage: family_build.sh <outdir> <family> <Style>=<TAG> ...
#   e.g. family_build.sh $R/family-titilliumweb titilliumweb \
#          TitilliumWeb-Regular=fstype-r2 ... TitilliumWeb-ExtraLight=fstype-r3
# Reads  $S/baseline/<Style>-<TAG>/sources/<Style>.glyphs  (S = scratch root below)
# Writes <outdir>/<Style>.gate.txt and <outdir>/summary.tsv; builds in $S/family-<family>.
set -uo pipefail
S=/home/fsanches/compartilhado/sfd-reland-scratch/fstype
B3=/home/fsanches/compartilhado/builder3-worktrees/main-e851b8b/target/release/gftools-builder
D3=/home/fsanches/compartilhado/diffenator3-venv/bin/diffenator3
PY=/home/fsanches/compartilhado/gftools/venv/bin/python3
TG=/home/fsanches/compartilhado/sfd-batch5/tools/table_gate.py
FAM=/home/fsanches/compartilhado/gf-source-modernization/investigations/next-fstype/runs/families-fstype.tsv
out=$1; fam=$2; shift 2
d=$S/family-$fam; rm -rf "$d"; mkdir -p "$d/sources" "$out"
{ echo "buildVariable: false"; echo "removeOutlineOverlaps: false"; echo "sources:"; } > "$d/sources/config.yaml"
for st in "$@"; do
  style=${st%%=*}; tag=${st#*=}
  cp "$S/baseline/$style-$tag/sources/$style.glyphs" "$d/sources/" || exit 2
  echo "  - $style.glyphs" >> "$d/sources/config.yaml"
done
(cd "$d" && timeout 1800 "$B3" sources/config.yaml) > "$out/build.log" 2>&1 || { echo "BUILD FAILED" >&2; exit 1; }
ls "$d/fonts/ttf" > "$out/built-files.txt"
: > "$out/summary.tsv"
for st in "$@"; do
  style=${st%%=*}
  shipped=$(awk -F'\t' -v s="$style" 'NR>1 && $7==s {print $9}' "$FAM")
  built="$d/fonts/ttf/$(basename "$shipped")"
  if [ ! -f "$built" ]; then printf '%s\tNOT-BUILT\t%s\n' "$style" "$(basename "$shipped")" >> "$out/summary.tsv"; continue; fi
  "$D3" -J 1 --no-languages --no-match --json --succinct "$shipped" "$built" > "$d/$style.d3.json" 2>/dev/null
  "$PY" "$TG" "$d/$style.d3.json" --fonts "$shipped" "$built" > "$out/$style.gate.txt" 2>&1
  n=$(sed -n 's/^\([0-9]\{1,\}\) blocking table difference(s).*/\1/p' "$out/$style.gate.txt" | tail -1)
  printf '%s\t%s\t%s\n' "$style" "${n:-GATE-DID-NOT-FINISH}" "$(basename "$built")" >> "$out/summary.tsv"
done
cat "$out/summary.tsv"
