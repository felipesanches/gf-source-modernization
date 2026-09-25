#!/bin/bash
# Question answered: between my `before` gate (unmodified source, BF 17ea899) and each
# later set (altuni / blues / final / final-workarounds / siblings-altuni), which gate
# lines disappeared or appeared? Anything other than the targeted BLOCKING rows and the
# closing summary line would be an unintended effect of the change.
# Run: bash nothing_else_opened.sh > ../runs/nothing_else_opened.txt
H=$(cd "$(dirname "$0")/.." && pwd)
B=/home/fsanches/compartilhado/sfd-reland/baseline-next
for set_ in altuni blues final final-workarounds siblings-altuni; do
  for g in "$H"/runs/$set_/*.gate.txt; do
    s=$(basename "$g" .gate.txt)
    ref="$H/runs/before/$s.gate.txt"; [ -e "$ref" ] || ref="$B/$s.gate.txt"
    d=$(diff <(grep -v '^flags:\|^from:\|^workarounds:\|^usWeightClass\|^ *$' "$ref" | grep -E '^( *BLOCKING|RELEASE-STALE|[0-9]+ blocking|GAINED|LOST|INFO|WARN)' ) \
             <(grep -v '^flags:\|^from:\|^workarounds:\|^usWeightClass\|^ *$' "$g" | grep -E '^( *BLOCKING|RELEASE-STALE|[0-9]+ blocking|GAINED|LOST|INFO|WARN)') | grep '^[<>]')
    echo "== $set_ $s (vs $(basename $(dirname $ref))):"
    printf '%s\n' "$d" | sed 's/^/   /'
  done
done
