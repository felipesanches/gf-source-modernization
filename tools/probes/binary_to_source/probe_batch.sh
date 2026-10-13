#!/bin/sh
# Question answered: for each family named in <worklist>, does converting its shipped fonts
# with babelfont and building them give back the release (probe.py's verdict per style)?
# One family at a time, smallest fonts first; each family gets <scratch>/<family>/ and a log,
# and <scratch>/summary.tsv gets one line per family: family, styles, CLEAN/RESIDUAL/... counts.
#
#   BF=<babelfont> B3=<gftools-builder> sh probe_batch.sh <google/fonts> <worklist> <scratch>
#
# <worklist>: family directory names (ofl/apache/ufl subdirectory names), whitespace-separated.
set -eu
GF=${1:?google/fonts checkout}; LIST=${2:?worklist}; S=${3:?scratch dir}
HERE=$(cd "$(dirname "$0")" && pwd)
PY=${PY:-python3}
mkdir -p "$S"
# order by the largest glyph count among each family's fonts
for f in $(cat "$LIST"); do
  d=$(ls -d "$GF"/ofl/"$f" "$GF"/apache/"$f" "$GF"/ufl/"$f" 2>/dev/null | head -1)
  n=$("$PY" -c "import sys
from fontTools.ttLib import TTFont
print(max(TTFont(p, lazy=True)['maxp'].numGlyphs for p in sys.argv[1:]))" "$d"/*.ttf)
  echo "$n $f $d"
done | sort -n > "$S/order.txt"
while read -r n f d; do
  [ -s "$S/$f.log" ] && grep -q "^done" "$S/$f.log" && continue   # resumable
  mkdir -p "$S/$f"
  "$PY" "$HERE/probe.py" "$S/$f" "$d"/*.ttf > "$S/$f.log" 2>&1 || true
  echo "done" >> "$S/$f.log"
  styles=$(ls "$d"/*.ttf | wc -l)
  # verdict lines start at column 0 (stem, then CLEAN: / RESIDUAL: / CONVERT FAILED / BUILD FAILED)
  verdicts=$(grep -E '^[^ ]' "$S/$f.log" | grep -v '^done$' | awk '{sub(":", "", $2); print $2}' \
    | sort | uniq -c | awk '{printf "%s%s=%s", (NR>1?",":""), $2, $1}')
  printf '%s\t%s\t%s\t%s\n' "$f" "$styles" "$n" "$verdicts" >> "$S/summary.tsv"
done < "$S/order.txt"
