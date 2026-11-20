#!/bin/sh
# Question: do the googlefonts forks of the googlefontdirectory-hg families hold the same
# src/ .sfd and .vfb files as googlefontdirectory-hg at the commit google/fonts recorded
# (52f780bc)? (tools/metadata.py legacy_fork states "hold the same files".)
# Compares git blob ids: the fork at the base commit families-binary.tsv records vs
# googlefontdirectory-hg:ofl/<family>/src/<file>. Prints one line per file: same / DIFFERS.
# Usage: sh same_src.sh <repo>...   (landed clones in sfd-reland-repos; repo archive mirror)
H=${HG:-/home/fsanches/compartilhado/upstream_repos/repo_archive/googlefonts/googlefontdirectory-hg.git}
HGREV=${HGREV:-52f780bc9d197280a9f430574e179a5f233c56b6}
W=$(cd "$(dirname "$0")/../../.." && pwd)
for d in "$@"; do
  D=/home/fsanches/compartilhado/sfd-reland-repos/$d
  c=$(awk -F'\t' -v r="$d" '$1==r {print $6; exit}' "$W/families-binary.tsv")
  for f in $(git -C "$D" ls-tree -r --name-only "$c" -- src | grep -iE '\.(sfd|vfb)$'); do
    a=$(git -C "$D" rev-parse "$c:$f"); b=$(git -C "$H" rev-parse "$HGREV:ofl/$d/$f" 2>/dev/null)
    [ "$a" = "$b" ] && echo "$d $f same" || echo "$d $f DIFFERS"
  done
done
