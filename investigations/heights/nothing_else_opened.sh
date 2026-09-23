#!/bin/bash
# Did an edit change any gate line OTHER than the OS/2 height rows? Compares each
# style's after-ca43adc gate with its before-ca43adc gate, height rows and the
# closing count line excluded. Empty diff = nothing else opened or closed.
H=$(cd "$(dirname "$0")" && pwd)
for g in "$H"/runs/after-ca43adc/*.gate.txt; do
  s=$(basename "$g")
  echo "== $s"
  diff <(grep -vE 'OS/2\.(sx_height|s_cap_height)|blocking table difference' "$H/runs/before-ca43adc/$s") \
       <(grep -vE 'OS/2\.(sx_height|s_cap_height)|blocking table difference' "$g") && echo "   identical apart from the height rows"
done
