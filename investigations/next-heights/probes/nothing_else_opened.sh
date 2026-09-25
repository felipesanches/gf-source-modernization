#!/bin/bash
# Question answered: did a proposed change (a run set) alter ANY gate line other than
# the rows it is meant to close? For each style, the gate of runs/<after>/ minus the
# closed rows must equal the gate of runs/<before>/ minus the same rows, line for
# line (the "flags:" line and babelfont's own log lines are ignored; RELEASE-STALE
# and BLOCKING lines and the closing summary line are compared, the summary with its
# counts removed).
#
# Run: bash nothing_else_opened.sh <before-set> <after-set> [Style...]
set -uo pipefail
H=$(cd "$(dirname "$0")/.." && pwd)
B=$H/runs/$1; A=$H/runs/$2; shift 2
styles=${*:-$(ls "$A"/*.gate.txt | xargs -n1 basename | sed 's/\.gate\.txt$//')}
closed='^BLOCKING (OS/2\.sx_height|OS/2\.s_cap_height|hmtx\.uni00A0) '
norm() { grep -E '^(BLOCKING|RELEASE-STALE|[0-9]+ blocking)' "$1" | grep -Ev "$closed" |
         sed -E 's/^[0-9]+ blocking table difference\(s\), [0-9]+ stale in the release.*/SUMMARY/'; }
for s in $styles; do
  if diff <(norm "$B/$s.gate.txt") <(norm "$A/$s.gate.txt") >/dev/null; then
    echo "$s: identical apart from the closed rows ($(grep -cE "$closed" "$B/$s.gate.txt") -> $(grep -cE "$closed" "$A/$s.gate.txt") height/nbsp rows)"
  else
    echo "$s: OTHER LINES CHANGED"; diff <(norm "$B/$s.gate.txt") <(norm "$A/$s.gate.txt") | sed 's/^/    /'
  fi
done
