#!/bin/bash
# kern_scan.sh -- does any other build kern differently from its release?
#
# Question answered: the table gate accepts every GPOS difference when both fonts carry
# lookups ("a legacy kern modernised into GPOS"). For every build kept in a scratch
# baseline directory, paired with its release by the pairing table (families-next.tsv
# for *-next, families.tsv for *-first), how many same-script letter pairs
# (probes/shaping_compare.py corpus "pairs") and kerned pairs with a mark between
# ("kern+mark") shape differently under HarfBuzz?
# Usage: bash kern_scan.sh > runs/kern_scan.tsv
PY=/home/fsanches/compartilhado/gftools/venv/bin/python3
U=/home/fsanches/compartilhado/sfd-reland/investigations/next-cardo
scan() {  # root suffix families
  for d in "$1"/*"$2"; do
    style=$(basename "$d"); style=${style%$2}
    built=$(ls "$d"/fonts/ttf/*.ttf 2>/dev/null | head -1); [ -n "$built" ] || continue
    shipped=$(awk -F'\t' -v s="$style" 'NR>1 && $7==s {print $9}' "$3"); [ -n "$shipped" ] || continue
    echo "$style|$shipped|$built"
  done
}
{ scan /home/fsanches/compartilhado/sfd-reland-scratch/baseline -next /home/fsanches/compartilhado/sfd-reland/families-next.tsv
  scan /home/fsanches/compartilhado/sfd-reland-scratch/emptygpos/baseline -first /home/fsanches/compartilhado/sfd-reland/families.tsv
} | xargs -P 3 -I{} bash -c 'IFS="|" read -r s a b <<<"{}"; r=$('"$PY"' '"$U"'/probes/shaping_compare.py "$a" "$b" --show 0 --only pairs,kern+mark 2>&1 | tr "\n" " "); printf "%s\t%s\t%s\n" "$s" "$r" "$b"'
