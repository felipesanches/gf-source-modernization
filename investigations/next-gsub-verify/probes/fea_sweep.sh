#!/bin/bash
# Question answered: across EVERY style of both batches (families.tsv, families-next.tsv),
# which conversions does the proposed babelfont language-system change alter at all?
# Converts each style's unmodified, paired .sfd with the integration converter (17ea899)
# and with the prototype (17ea899 + next-gsub/probes/babelfont-17ea899-langsys-as-built.diff,
# built by the verifier from its own scratch clone, BUILT_FROM d345b49), using the
# style's own recipe flags (tools/recipe.py), and compares the two .glyphs files'
# feature code (featurePrefixes/classes/features blocks) byte for byte, plus whether the
# prototype logged its aalt warn-only line. Conversion only: nothing is compiled.
#
# Usage: bash fea_sweep.sh > ../runs/fea_sweep.tsv
set -uo pipefail
W=/home/fsanches/compartilhado/gf-source-modernization
ARC=/home/fsanches/compartilhado/upstream_repos/repo_archive
PY=/home/fsanches/compartilhado/gftools/venv/bin/python3
SC=/home/fsanches/compartilhado/sfd-reland-scratch/gsub-verify/fea-sweep
BFI=/home/fsanches/compartilhado/babelfont-rs-worktrees/integration-ff-prs/target-heights/release/babelfont
BFP=/home/fsanches/compartilhado/sfd-reland-scratch/gsub-verify/bf-target/release/babelfont
mkdir -p "$SC"
printf 'table\tstyle\tfea\taalt_warning\n'
for T in "$W/families.tsv" "$W/families-next.tsv"; do
  tail -n +2 "$T" | while IFS=$'\t' read -r repo fam lic kind base commit style src shipped; do
    d="$SC/$(basename "$T" .tsv)/$style"; mkdir -p "$d"
    if [ "$kind" = hg ]; then p="$lic/$fam/$src"; else p="$src"; fi
    git -C "$ARC/$base.git" show "$commit:$p" > "$d/src.sfd" 2>/dev/null || { printf '%s\t%s\tNO-SOURCE\t-\n' "$(basename "$T")" "$style"; continue; }
    mapfile -t flags < <(FAMILIES="$T" "$PY" "$W/tools/recipe.py" "$style" 2>/dev/null)
    "$BFI" "$d/src.sfd" "$d/base.glyphs" "${flags[@]}" > "$d/base.log" 2>&1
    "$BFP" "$d/src.sfd" "$d/proto.glyphs" "${flags[@]}" > "$d/proto.log" 2>&1
    if [ ! -s "$d/base.glyphs" ] || [ ! -s "$d/proto.glyphs" ]; then
      printf '%s\t%s\tCONVERT-FAILED\t-\n' "$(basename "$T")" "$style"; continue; fi
    if cmp -s "$d/base.glyphs" "$d/proto.glyphs"; then fea=identical; else fea=CHANGED; fi
    warn=$(grep -c 'aalt is registered for fewer language systems' "$d/proto.log")
    printf '%s\t%s\t%s\t%s\n' "$(basename "$T")" "$style" "$fea" "$warn"
  done
done
