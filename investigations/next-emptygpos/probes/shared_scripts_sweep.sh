#!/bin/bash
# Question answered: if the recipe passed builder3 `sharedLayoutScripts: true` for every
# style whose release FontForge exported in OpenType mode (FFTM present, and GSUB or GPOS
# present), which gate rows would open or close, style by style?
#
# The option changes nothing but the GSUB/GPOS script lists (runs/03 vs runs/04: the
# flag-off prototype build differs from the pinned one only in head.modified and the
# name-ID-5 build stamp; flag-on differs only in GPOS or GSUB), and ff_shared_scripts.py
# `emulate` builds exactly the prototype's tables (runs/04 and runs/01: `compare` SAME).
# So this applies the emulation to EXISTING fidelity-only builds and re-gates them,
# instead of rebuilding every style.
#
#   BUILDS=<dir holding <Style>-<tag>/fonts/ttf/*.ttf>  TAG=<suffix, e.g. next>
#   FAMILIES=<pairing.tsv>  CENSUS=<runs/census_layout_shells.tsv>  OUT=<dir>
#   bash shared_scripts_sweep.sh
# Output: $OUT/<Style>.off.txt / .on.txt (gate text) and one TSV row per style on stdout:
#   style  rows_off  rows_on  opened  closed
set -uo pipefail
PY=/home/fsanches/compartilhado/gftools/venv/bin/python3
D3=/home/fsanches/compartilhado/diffenator3-venv/bin/diffenator3
TG=/home/fsanches/compartilhado/sfd-batch5/tools/table_gate.py
P=$(cd "$(dirname "$0")" && pwd)
mkdir -p "$OUT"
printf 'style\trows_off\trows_on\topened\tclosed\n'
tail -n +2 "$FAMILIES" | while IFS=$'\t' read -r repo fam lic kind base commit style src shipped; do
  cls=$(awk -F'\t' -v s="$style" '$2==s{print $3"\t"$4}' "$CENSUS" | head -1)
  case "$cls" in -*) continue;; esac                       # not FontForge-exported
  case "$cls" in *kern-only*|*no-layout*) continue;; esac  # not OpenType mode
  built=$(ls "$BUILDS/$style-$TAG"/fonts/ttf/*.ttf 2>/dev/null | head -1)
  [ -n "$built" ] || { printf '%s\tNO-BUILD\t-\t-\t-\n' "$style"; continue; }
  on="$OUT/$style.on.ttf"
  "$PY" "$P/ff_shared_scripts.py" emulate "$built" "$on" > /dev/null
  for v in off on; do
    f=$built; [ $v = on ] && f=$on
    "$D3" -J 1 --no-languages --no-match --json --succinct "$shipped" "$f" > "$OUT/$style.$v.d3.json" 2>/dev/null
    "$PY" "$TG" "$OUT/$style.$v.d3.json" --fonts "$shipped" "$f" > "$OUT/$style.$v.txt" 2>&1
    rm -f "$OUT/$style.$v.d3.json"
  done
  rows() { awk '/^ *BLOCKING /{print $2}' "$1" | sort -u; }
  opened=$(comm -13 <(rows "$OUT/$style.off.txt") <(rows "$OUT/$style.on.txt") | paste -sd, -)
  closed=$(comm -23 <(rows "$OUT/$style.off.txt") <(rows "$OUT/$style.on.txt") | paste -sd, -)
  printf '%s\t%s\t%s\t%s\t%s\n' "$style" "$(rows "$OUT/$style.off.txt" | grep -c .)" \
    "$(rows "$OUT/$style.on.txt" | grep -c .)" "${opened:--}" "${closed:--}"
  rm -f "$on"
done
