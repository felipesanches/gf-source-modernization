#!/bin/sh
# Question: does a babelfont build convert each family's .vfb to the underline position the
# release has (post.underlinePosition)? Families: the arguments (repos in families-vfb.tsv).
# Usage: sh underline_check.sh <babelfont binary> <scratch dir> <repo>...
set -eu
BF=${1:?babelfont}; S=${2:?scratch}; shift 2
W=$(cd "$(dirname "$0")/../../.." && pwd); A=/home/fsanches/compartilhado/upstream_repos/repo_archive
PY=/home/fsanches/compartilhado/gftools/venv/bin/python3
mkdir -p "$S"
for r in "$@"; do
  awk -F'\t' -v r="$r" '$1==r{print $2"\t"$3"\t"$4"\t"$5"\t"$6"\t"$8"\t"$9}' "$W/families-vfb.tsv" | head -1 |
  while IFS='	' read -r fam lic kind base commit src shipped; do
    if [ "$kind" = hg ]; then git -C "$A/$base.git" show "$commit:$lic/$fam/$src" > "$S/$r.vfb" 2>/dev/null || git -C "$A/$base.git" show "$commit:$fam/$src" > "$S/$r.vfb"
    else git -C "$A/$base.git" show "$commit:$src" > "$S/$r.vfb"; fi
    "$BF" "$S/$r.vfb" "$S/$r.glyphs" > /dev/null 2>&1
    got=$(grep -A1 "name = underlinePosition;" "$S/$r.glyphs" | grep -o "value = -*[0-9]*" | head -1 | sed 's/value = //')
    rel=$("$PY" -I -c "from fontTools.ttLib import TTFont; print(TTFont('$shipped', lazy=True)['post'].underlinePosition)")
    echo "$r release=$rel converted=$got $([ "$got" = "$rel" ] && echo OK || echo DIFF)"
  done
done
