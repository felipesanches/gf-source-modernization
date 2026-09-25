#!/bin/bash
# Question answered: does a proposed change alter ANYTHING in the converted .glyphs
# besides the rows it targets? Converts each style twice with the recipe's own flags
# (tools/recipe.py, families-next.tsv) and prints the unified diff of the two .glyphs.
#
#   bash glyphs_diff.sh blues   BF 17ea899: unmodified source vs my edited copy
#                               (<scratch>/edits/<Style>.sfd, make_edits.py)
#   bash glyphs_diff.sh altuni  unmodified source: BF 17ea899 vs my patched build
#
# Output: ../runs/glyphs_diff-<mode>.txt
set -uo pipefail
H=$(cd "$(dirname "$0")/.." && pwd)
W=/home/fsanches/compartilhado/sfd-reland
S=/home/fsanches/compartilhado/sfd-reland-scratch/heights-verify
PY=/home/fsanches/compartilhado/gftools/venv/bin/python3
BF0=/home/fsanches/compartilhado/babelfont-rs-worktrees/integration-ff-prs/target-heights/release/babelfont
BF1=$S/bf-target/release/babelfont
ARC=/home/fsanches/compartilhado/upstream_repos/repo_archive/googlefonts/googlefontdirectory-hg.git
export FAMILIES=$W/families-next.tsv
mode=$1
case $mode in
  blues) styles="Ledger-Regular LilitaOne-Regular Lustria-Regular Magra-Bold MergeOne-Regular OleoScript-Bold OleoScript-Regular OleoScriptSwashCaps-Bold OleoScriptSwashCaps-Regular Rambla-Bold Rambla-BoldItalic Sail-Regular TextMeOne-Regular" ;;
  altuni) styles="KottaOne-Regular Macondo-Regular Rosarivo-Italic Ledger-Regular LilitaOne-Regular Lustria-Regular Magra-Bold MergeOne-Regular OleoScript-Bold OleoScript-Regular OleoScriptSwashCaps-Bold OleoScriptSwashCaps-Regular Rambla-Bold Rambla-BoldItalic Sail-Regular TextMeOne-Regular Magra-Regular Rambla-Italic Rambla-Regular Rosarivo-Regular" ;;
  *) echo "mode: blues|altuni" >&2; exit 2 ;;
esac
D=$S/glyphs-diff-$mode; mkdir -p "$D"
out=$H/runs/glyphs_diff-$mode.txt; : > "$out"
for s in $styles; do
  row=$(awk -F'\t' -v s="$s" 'NR>1 && $7==s' "$FAMILIES")
  IFS=$'\t' read -r repo fam lic kind base commit _ src shipped <<<"$row"
  git -C "$ARC" show "$commit:$lic/$fam/$src" > "$D/$s.orig.sfd"
  mapfile -t flags < <("$PY" "$W/tools/recipe.py" "$s")
  if [ "$mode" = blues ]; then
    "$BF0" "$D/$s.orig.sfd" "$D/$s.a.glyphs" "${flags[@]}" >/dev/null 2>&1
    "$BF0" "$S/edits/$s.sfd" "$D/$s.b.glyphs" "${flags[@]}" >/dev/null 2>&1
  else
    "$BF0" "$D/$s.orig.sfd" "$D/$s.a.glyphs" "${flags[@]}" >/dev/null 2>&1
    "$BF1" "$D/$s.orig.sfd" "$D/$s.b.glyphs" "${flags[@]}" >/dev/null 2>&1
  fi
  echo "=== $s" >> "$out"
  diff -u "$D/$s.a.glyphs" "$D/$s.b.glyphs" | grep '^[-+]' | grep -v '^\(---\|+++\)' >> "$out"
done
cat "$out"
