#!/bin/bash
# run_stage.sh -- one measured stage of the cardo unit.
#
# Question answered: with a given converter build, a given (possibly edited) .sfd and
# the toolchain workarounds tools/land.py applies, which rows block for one Cardo
# style -- under the shared gate (baseline.sh's verdict) AND under the gate with this
# unit's proposed arbitration (probes/table_gate_proposed.py) -- and does the build
# SHAPE like the release (probes/shaping_compare.py, which catches what the gate's
# GPOS arbitration waves through)?
#
# Usage: bash run_stage.sh <Style> <stage-name> [<edited.sfd>]
#   env: BFBIN=<babelfont binary>   (default: the integration-ff-prs build =
#        upstream main 496e904 + babelfont-rs PRs #91/#92/#93)
#        WORKAROUNDS=1              run it through next-fstype's bf_with_workarounds.sh
#                                   (usWeightClass from TTFWeight, as land.py does)
# Output: runs/<stage-name>/<Style>.{tsv,gate.txt,proposed.txt,shaping.txt}
set -uo pipefail
W=/home/fsanches/compartilhado/sfd-reland
U=$W/investigations/next-cardo
PY=/home/fsanches/compartilhado/gftools/venv/bin/python3
style=$1; stage=$2; src=${3:-}
BFBIN=${BFBIN:-/home/fsanches/compartilhado/babelfont-rs-worktrees/integration-ff-prs/target-heights/release/babelfont}
out=$U/runs/$stage; mkdir -p "$out"
export FAMILIES=$W/families-next.tsv SCRATCH=/home/fsanches/compartilhado/sfd-reland-scratch/cardo
if [ "${WORKAROUNDS:-0}" = 1 ]; then
  export REAL_BF=$BFBIN BF=$W/investigations/next-fstype/probes/bf_with_workarounds.sh
else
  export BF=$BFBIN
fi
tag=cardo-$stage
if [ -n "$src" ]; then export SRC_OVERRIDE=$src; else unset SRC_OVERRIDE; fi
OUT=$out TAG=$tag bash $W/tools/baseline.sh "$style"
echo "converter: $BFBIN (sha256 $(sha256sum "$BFBIN" | cut -c1-16))${src:+; source: $src (sha256 $(sha256sum "$src" | cut -c1-16))}; workarounds=${WORKAROUNDS:-0}" >> "$out/$style.gate.txt"
d=$SCRATCH/baseline/$style-$tag
shipped=$(awk -F'\t' -v s="$style" 'NR>1 && $7==s {print $9}' "$FAMILIES")
built=$(ls "$d"/fonts/ttf/*.ttf 2>/dev/null | head -1)
[ -n "$built" ] || { echo "$style $stage: no build"; exit 1; }
$PY $U/probes/table_gate_proposed.py "$d/d3.json" --fonts "$shipped" "$built" > "$out/$style.proposed.txt" 2>&1
$PY $U/probes/shaping_compare.py "$shipped" "$built" "$d/d3.json" --show 3 > "$out/$style.shaping.txt" 2>&1
echo "$style $stage: shared gate $(cut -f3,4 "$out/$style.tsv" | tr '\t' ' '); proposed gate: $(tail -1 "$out/$style.proposed.txt")"
grep -E "^(base|pairs|kern|words)" "$out/$style.shaping.txt" | sed 's/^/   shaping /'
