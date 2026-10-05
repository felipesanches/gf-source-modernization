#!/bin/bash
# proposed_gate_sweep.sh -- which verdicts would the proposed gate change?
#
# Question answered: for every baseline-next build kept in the scratch baseline
# directory (sfd-reland-scratch/baseline/<Style>-next, paired with its release by
# families-next.tsv), how many rows block under the shared gate
# (sfd-batch5/tools/table_gate.py 2f43693) and under probes/table_gate_proposed.py?
# Usage: bash proposed_gate_sweep.sh > runs/proposed_gate_sweep.tsv
PY=/home/fsanches/compartilhado/gftools/venv/bin/python3
U=/home/fsanches/compartilhado/gf-source-modernization/investigations/next-cardo
TG=/home/fsanches/compartilhado/sfd-batch5/tools/table_gate.py
F=/home/fsanches/compartilhado/gf-source-modernization/families-next.tsv
for d in /home/fsanches/compartilhado/sfd-reland-scratch/baseline/*-next; do
  s=$(basename "$d"); s=${s%-next}
  b=$(ls "$d"/fonts/ttf/*.ttf 2>/dev/null | head -1); [ -n "$b" ] && [ -s "$d/d3.json" ] || continue
  a=$(awk -F'\t' -v s="$s" 'NR>1 && $7==s {print $9}' "$F"); [ -n "$a" ] || continue
  echo "$s|$a|$b|$d/d3.json"
done | xargs -P 3 -I{} bash -c 'IFS="|" read -r s a b j <<<"{}"; o=$('"$PY"' '"$TG"' "$j" --fonts "$a" "$b" 2>&1 | tail -1 | cut -d" " -f1); n=$('"$PY"' '"$U"'/probes/table_gate_proposed.py "$j" --fonts "$a" "$b" 2>&1 | tail -1 | cut -d" " -f1); printf "%s\t%s\t%s\n" "$s" "$o" "$n"'
