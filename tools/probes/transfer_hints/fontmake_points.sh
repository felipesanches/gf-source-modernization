#!/bin/sh
# Question: built from the same .glyphs sources with a compiler that keeps the points a source
# states (fontmake / ufo2ft, dropImpliedOnCurves=False), how many instructed glyphs still have
# points that are not the release's, and why (why_points_differ.py)?
# Usage: sh fontmake_points.sh <scratch dir of run.sh> <python with fontmake>
#   builds <scratch>/<repo>/fm/ from <scratch>/<repo>/sources/*.glyphs (instances; overlaps and
#   contour direction kept, as the fontc builds keep them: reverseOutlineDirection false)
#   and compares each font with the shipped font of the same name.
set -u
S=${1:?scratch}; PYFM=${2:?python with fontmake}
GF=${GF:-/home/fsanches/compartilhado/google/fonts}
HERE=$(cd "$(dirname "$0")" && pwd)
for d in "$S"/*/sources; do
  r=$(basename "$(dirname "$d")")
  out="$S/$r/fm"
  if [ ! -d "$out" ]; then
    mkdir -p "$out"
    for g in "$d"/*.glyphs; do
      "$PYFM" -m fontmake -g "$g" -i -o ttf --keep-overlaps --keep-direction --output-dir "$out" > "$out/build.log" 2>&1 || echo "== $r: fontmake failed on $(basename "$g")"
    done
  fi
  for f in "$out"/*.ttf; do
    [ -f "$f" ] || continue
    n=$(basename "$f")
    shipped=$(ls "$GF/ofl/$r/$n" "$GF/apache/$r/$n" "$GF/ufl/$r/$n" 2>/dev/null | head -1)
    [ -n "$shipped" ] || { echo "$r $n no shipped font of that name"; continue; }
    echo "$r $n $("$PYFM" -I "$HERE/why_points_differ.py" "$shipped" "$f" 2>&1 | tail -1)"
  done
done
