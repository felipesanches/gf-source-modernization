#!/bin/sh
# Question answered: at which commits of an upstream repository are the binaries google/fonts
# ships byte-identical files? (Matched by git blob hash, so only exact copies count.)
#
#   sh shipped_in_repo.sh <google/fonts checkout> <family dir, e.g. ofl/intelonemono> <bare mirror> [rev-list args]
#
# Prints, per commit holding at least one shipped .ttf blob, "<commit> <date> <subject> matches=N".
# Default rev-list args: --all (every ref of the mirror). Use e.g. "--first-parent main" for one line.
set -eu
GF=${1:?google/fonts}; FAM=${2:?family dir}; M=${3:?mirror}; shift 3
[ $# -gt 0 ] || set -- --all
T=$(mktemp "${TMPDIR:-/tmp}/shipped.XXXXXX")
git -C "$GF" ls-tree upstream/main "$FAM/" | awk '$4 ~ /\.ttf$/ {print $3}' > "$T"
echo "$(wc -l < "$T") shipped .ttf in $FAM"
for c in $(git -C "$M" rev-list --reverse "$@"); do
  n=$(git -C "$M" ls-tree -r "$c" | awk '{print $3}' | grep -c -F -f "$T" || true)
  [ "$n" -gt 0 ] && echo "$(git -C "$M" log -1 --format='%h %ad %s' --date=short "$c") matches=$n"
done
rm -f -- "${T:?}"
