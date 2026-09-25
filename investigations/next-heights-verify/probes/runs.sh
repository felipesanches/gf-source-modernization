#!/bin/bash
# Question answered (adversarial re-verification of unit "heights", next batch):
# for each style, which blocking table rows does the pipeline's own harness
# (tools/baseline.sh, one build per style, paired by construction through
# families-next.tsv) report for a given (converter, source) combination?
#
#   before  BF = integration-ff-prs 17ea899 (upstream 496e904 + babelfont #91/#92/#93),
#           unmodified sources. Must equal baseline-next/ gate for gate.
#   altuni  BF = my own scratch build of 17ea899 + the investigator's patch
#           ../../next-heights/probes/babelfont-altuni-lookup.patch (built from a
#           `git archive` export, not the investigator's worktree), unmodified sources.
#   blues   BF = 17ea899, sources edited by MY OWN edit script (make_edits.sh here),
#           BlueValues re-derived independently from src/<X>.otf with fontTools.
#   final   patched BF + my edits.
#
# Run:  bash runs.sh <set> [Style...]
# Out:  ../runs/<set>/<Style>.{tsv,gate.txt,src}
set -uo pipefail
H=$(cd "$(dirname "$0")/.." && pwd)
W=/home/fsanches/compartilhado/sfd-reland
S=/home/fsanches/compartilhado/sfd-reland-scratch/heights-verify
EDITS=${EDITS:-$S/edits}
BF0=/home/fsanches/compartilhado/babelfont-rs-worktrees/integration-ff-prs/target-heights/release/babelfont
BF1=${BF1:-$S/bf-target/release/babelfont}
export FAMILIES=$W/families-next.tsv SCRATCH=$S

ALL="KottaOne-Regular Ledger-Regular LilitaOne-Regular Lustria-Regular Macondo-Regular
Magra-Bold MergeOne-Regular OleoScript-Bold OleoScript-Regular OleoScriptSwashCaps-Bold
OleoScriptSwashCaps-Regular Rambla-Bold Rambla-BoldItalic Rosarivo-Italic Sail-Regular
TextMeOne-Regular"

set_=$1; shift
styles=${*:-$ALL}
case $set_ in
  before|blues|siblings) export BF=$BF0 ;;
  altuni|final|siblings-altuni) export BF=$BF1 ;;
  *) echo "unknown set $set_" >&2; exit 2 ;;
esac
export OUT=$H/runs/$set_ TAG=heights-verify-$set_
mkdir -p "$OUT"
for s in $styles; do
  src=
  if [ "$set_" = blues ] || [ "$set_" = final ]; then
    [ -e "$EDITS/$s.sfd" ] && src=$EDITS/$s.sfd
  fi
  if [ -n "$src" ]; then
    echo "SRC_OVERRIDE=$src sha256=$(sha256sum "$src" | cut -c1-16) BF=$BF" > "$OUT/$s.src"
    SRC_OVERRIDE=$src bash "$W/tools/baseline.sh" "$s"
  else
    echo "unmodified BF=$BF" > "$OUT/$s.src"
    bash "$W/tools/baseline.sh" "$s"
  fi
done
