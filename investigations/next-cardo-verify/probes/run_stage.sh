#!/bin/bash
# run_stage.sh -- one independently re-run stage of the cardo verification.
#
# Question answered: with a given converter binary (default: MY build of the cardo
# unit's prototype patch on 17ea899, in sfd-reland-scratch/cardo-verify/bf-target), an
# optional edited .sfd and optional land.py workarounds, what do the shared gate, the
# unit's proposed gate and the unit's HarfBuzz shaping comparison report for one Cardo
# style -- plus my multi-mark corpus (probes/multimark_compare.py), which the unit's
# corpus never exercised?
#
# Usage: bash run_stage.sh <Style> <stage-name> [<edited.sfd>]
#   env: BFBIN=<babelfont>  WORKAROUNDS=1  EXTRA_FLAGS=...  DROP_FLAGS=...
# Output: ../runs/<stage-name>/<Style>.{tsv,gate.txt,proposed.txt,shaping.txt,multimark.txt,layout.txt}
set -uo pipefail
W=/home/fsanches/compartilhado/gf-source-modernization
U=$W/investigations/next-cardo          # the unit under verification (its probes)
V=$W/investigations/next-cardo-verify
PY=/home/fsanches/compartilhado/gftools/venv/bin/python3
style=$1; stage=$2; src=${3:-}
BFBIN=${BFBIN:-/home/fsanches/compartilhado/sfd-reland-scratch/cardo-verify/bf-target/release/babelfont}
out=$V/runs/$stage; mkdir -p "$out"
export FAMILIES=$W/families-next.tsv SCRATCH=/home/fsanches/compartilhado/sfd-reland-scratch/cardo-verify
if [ "${WORKAROUNDS:-0}" = 1 ]; then
  export REAL_BF=$BFBIN BF=$W/investigations/next-fstype/probes/bf_with_workarounds.sh
else
  export BF=$BFBIN
fi
tag=cardo-verify-$stage
if [ -n "$src" ]; then export SRC_OVERRIDE=$src; else unset SRC_OVERRIDE; fi
OUT=$out TAG=$tag bash $W/tools/baseline.sh "$style"
echo "converter: $BFBIN (sha256 $(sha256sum "$BFBIN" | cut -c1-16))${src:+; source: $src (sha256 $(sha256sum "$src" | cut -c1-16))}; workarounds=${WORKAROUNDS:-0}; extra=${EXTRA_FLAGS:-}" >> "$out/$style.gate.txt"
d=$SCRATCH/baseline/$style-$tag
shipped=$(awk -F'\t' -v s="$style" 'NR>1 && $7==s {print $9}' "$FAMILIES")
built=$(ls "$d"/fonts/ttf/*.ttf 2>/dev/null | head -1)
[ -n "$built" ] || { echo "$style $stage: no build"; exit 1; }
$PY $U/probes/table_gate_proposed.py "$d/d3.json" --fonts "$shipped" "$built" > "$out/$style.proposed.txt" 2>&1
$PY $U/probes/shaping_compare.py "$shipped" "$built" "$d/d3.json" --show 3 > "$out/$style.shaping.txt" 2>&1
$PY $V/probes/multimark_compare.py "$shipped" "$built" --show 3 > "$out/$style.multimark.txt" 2>&1
$PY $V/probes/layout_summary.py "$built" > "$out/$style.layout.txt" 2>&1
echo "$style $stage: shared $(cut -f3,4 "$out/$style.tsv" | tr '\t' ' '); proposed: $(tail -1 "$out/$style.proposed.txt")"
grep -E "^(base|pairs|kern|words)" "$out/$style.shaping.txt" | sed 's/^/   shaping /'
sed 's/^/   multimark /' "$out/$style.multimark.txt" | grep -E 'strings'
