#!/bin/sh
# Question: which backlog families (not CLEAN, not pushed; hinting-only ones left out) land CLEAN,
# or closer to it, with babelfont-rs main as the converter instead of our pinned branches?
# Input: backlog.tsv (table, repo, ledger status, ledger detail as of 2026-11-19).
# Each family is landed with tools/land.py into scratch (OUT, LANDED and SCRATCH under <scratch>),
# one at a time; recipe flags main does not know are dropped by land.py (recipe.NOT_YET_UPSTREAM).
# Usage: [LAND_ARGS=--unpublished-converter] sh tools/probes/upstream_main_2026-11-19/sweep.sh <scratch dir> <babelfont-rs worktree> [backlog file]
#   -> <scratch>/results.tsv: table, repo, old status, old detail, new verdict line
set -u
S=${1:?scratch dir}; BT=${2:?babelfont-rs worktree with target-heights/release/babelfont}
W=$(cd "$(dirname "$0")/../../.." && pwd)
mkdir -p "$S/out" "$S/logs"
while IFS='	' read -r table repo old detail; do
  [ -n "$repo" ] || continue
  grep -q "^[^	]*	$repo	" "$S/results.tsv" 2>/dev/null && continue
  log="$S/logs/$repo.log"
  ( cd "$W" && BF_TREE="$BT" FAMILIES="$table" OUT="$S/out" LANDED="$S/landed.tsv" SCRATCH="$S/build" \
      timeout 3600 /home/fsanches/compartilhado/gftools/venv/bin/python3 -I tools/land.py "$repo" ${LAND_ARGS:-} > "$log" 2>&1 )
  new=$(grep -m1 "^$repo: " "$log" || tail -1 "$log")
  printf '%s\t%s\t%s\t%s\t%s\n' "$table" "$repo" "$old" "$detail" "$new" >> "$S/results.tsv"
  rm -rf -- "${S:?}/out/${repo:?}" "${S:?}/build"
done < "${3:-$W/tools/probes/upstream_main_2026-11-19/backlog.tsv}"
