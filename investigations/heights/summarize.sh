#!/bin/sh
# Print, per harness run under runs/, the blocking rows and the gate's closing line
# (a run without its "N blocking table difference(s)" line did not finish).
H=$(cd "$(dirname "$0")" && pwd)
for run in before-f725e6a before-ca43adc after-ca43adc; do
  for g in "$H"/runs/$run/*.gate.txt; do
    [ -e "$g" ] || continue
    s=$(basename "$g" .gate.txt)
    printf '%-15s %-27s %s | %s\n' "$run" "$s" \
      "$(grep '^BLOCKING' "$g" | sed 's/^BLOCKING //' | paste -sd';' -)" \
      "$(grep -E '^[0-9]+ blocking table difference' "$g" || echo 'GATE DID NOT FINISH')"
  done
done
