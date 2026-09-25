#!/bin/bash
# Question answered: does the proposed GSUB arbitration (table_gate_gsub_proposed.py)
# change the gate's verdict on any style OTHER than the ones it was written for, and
# does it change any row other than GSUB.* ?
#
# Regates every complete baseline-next harness run (the .d3.json and built font the
# harness already produced under $SCR/<Style>-next/, paired by construction with
# families-next.tsv) with the shared gate and with the proposed one, on identical
# inputs, and prints per style: blocking count shared -> proposed, and the rows that
# moved. No conversion or build is repeated.
#
# Run: bash gate_sweep.sh > ../runs/gate_sweep_next.tsv
set -uo pipefail
W=/home/fsanches/compartilhado/sfd-reland
SCR=${SCR:-/home/fsanches/compartilhado/sfd-reland-scratch/baseline}
PY=/home/fsanches/compartilhado/gftools/venv/bin/python3
TG=/home/fsanches/compartilhado/sfd-batch5/tools/table_gate.py
TP=$(cd "$(dirname "$0")" && pwd)/table_gate_gsub_proposed.py
one() {
  style=$1
  d=$SCR/$style-next
  shipped=$(awk -F'\t' -v s="$style" 'NR>1 && $7==s {print $9}' "$W/families-next.tsv")
  built=$(ls "$d"/fonts/ttf/*.ttf 2>/dev/null | head -1)
  [ -s "$d/d3.json" ] && [ -n "$built" ] && [ -n "$shipped" ] || { printf '%s\tSKIP\n' "$style"; return; }
  a=$("$PY" "$TG" "$d/d3.json" --fonts "$shipped" "$built" 2>&1)
  b=$("$PY" "$TP" "$d/d3.json" --fonts "$shipped" "$built" 2>&1)
  na=$(printf '%s\n' "$a" | sed -n 's/^\([0-9]*\) blocking table.*/\1/p')
  nb=$(printf '%s\n' "$b" | sed -n 's/^\([0-9]*\) blocking table.*/\1/p')
  ra=$(printf '%s\n' "$a" | awk '/^BLOCKING /{print $2}' | sort)
  rb=$(printf '%s\n' "$b" | awk '/^BLOCKING /{print $2}' | sort)
  gone=$(comm -23 <(echo "$ra") <(echo "$rb") | paste -sd, -)
  new=$(comm -13 <(echo "$ra") <(echo "$rb") | paste -sd, -)
  printf '%s\t%s\t%s\t%s\t%s\n' "$style" "${na:-?}" "${nb:-?}" "${gone:--}" "${new:--}"
}
export -f one; export W SCR PY TG TP
printf 'style\tshared\tproposed\trows_closed\trows_opened\n'
for d in "$SCR"/*-next; do b=$(basename "$d"); echo "${b%-next}"; done | xargs -P 3 -I{} bash -c 'one {}' | sort
