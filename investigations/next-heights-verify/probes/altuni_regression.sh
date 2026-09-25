#!/bin/bash
# Question answered: over EVERY style of both batches (families.tsv + families-next.tsv),
# what does the proposed #91 follow-up (AltUni lookup) change in the converted .glyphs,
# compared with the unpatched integration-ff-prs 17ea899? Conversion only, each style
# with its own recipe flags (tools/recipe.py), unmodified source.
# Prints per style: IDENTICAL, or the changed lines of the .glyphs (so any change
# other than x-height/cap-height would show).
#
# BF0 = integration-ff-prs/target-heights (BUILT_FROM 17ea899)
# BF1 = my scratch build of 17ea899 + ../../next-heights/probes/babelfont-altuni-lookup.patch
#
# Run: bash altuni_regression.sh > ../runs/altuni_regression.txt
set -uo pipefail
W=/home/fsanches/compartilhado/sfd-reland
S=/home/fsanches/compartilhado/sfd-reland-scratch/heights-verify
PY=/home/fsanches/compartilhado/gftools/venv/bin/python3
BF0=/home/fsanches/compartilhado/babelfont-rs-worktrees/integration-ff-prs/target-heights/release/babelfont
BF1=$S/bf-target/release/babelfont
ARC=/home/fsanches/compartilhado/upstream_repos/repo_archive
D=$S/regression; mkdir -p "$D"
n=0; nchg=0
for tsv in families.tsv families-next.tsv; do
  export FAMILIES=$W/$tsv
  tail -n +2 "$FAMILIES" | while IFS=$'\t' read -r repo fam lic kind base commit style src shipped; do
    if [ "$kind" = hg ]; then p="$lic/$fam/$src"; else p="$src"; fi
    f="$D/$tsv-$style.sfd"
    git -C "$ARC/$base.git" show "$commit:$p" > "$f" 2>/dev/null || { echo "$tsv $style NO-SOURCE"; continue; }
    mapfile -t flags < <("$PY" "$W/tools/recipe.py" "$style" 2>/dev/null)
    [ "${#flags[@]}" -gt 0 ] || { echo "$tsv $style RECIPE-FAILED"; continue; }
    "$BF0" "$f" "$D/$tsv-$style.a.glyphs" "${flags[@]}" >/dev/null 2>&1 || { echo "$tsv $style CONVERT-FAILED-BF0"; continue; }
    "$BF1" "$f" "$D/$tsv-$style.b.glyphs" "${flags[@]}" >/dev/null 2>&1 || { echo "$tsv $style CONVERT-FAILED-BF1"; continue; }
    if cmp -s "$D/$tsv-$style.a.glyphs" "$D/$tsv-$style.b.glyphs"; then
      echo "$tsv $style IDENTICAL"
    else
      echo "$tsv $style CHANGED: $(diff "$D/$tsv-$style.a.glyphs" "$D/$tsv-$style.b.glyphs" | grep '^[<>]' | tr '\n' ' ')"
    fi
  done
done
