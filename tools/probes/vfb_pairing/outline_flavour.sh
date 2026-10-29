#!/bin/sh
# Question answered: is each paired .vfb a quadratic (TrueType-flavoured) master, whose
# outlines can match the release point for point, or a cubic one, whose FontLab export
# was converted to quadratics by FontLab itself (decision D2: fontc's conversion differs
# by a few units on every curve)? Counts curve nodes in each landed .glyphs source.
#
# Usage: sh outline_flavour.sh <landed repos dir> > outline-flavour-<date>.tsv
set -u
printf 'repo\tstyle\tcubic_nodes\tquadratic_nodes\tflavour\n'
for d in "$1"/*/; do
  d=${d%/}
  for g in "$d"/sources/*.glyphs; do
    [ -f "$g" ] || continue
    c=$(grep -c ',c)\|,cs)' "$g"); q=$(grep -c ',q)\|,qs)' "$g")
    if [ "$c" -gt "$q" ]; then f=cubic; elif [ "$q" -gt 0 ]; then f=quadratic; else f=lines-only; fi
    printf '%s\t%s\t%s\t%s\t%s\n' "$(basename "$d")" "$(basename "$g" .glyphs)" "$c" "$q" "$f"
  done
done
