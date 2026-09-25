#!/bin/bash
# run_all.sh -- every harness run of the fstype re-verification, one build per style.
#
# Question answered: reproduced independently (own pairing table, own candidates from
# make_verify_inputs.sh, own workaround wrapper), which gate rows does each stage leave?
#   v0-unmodified   plain converter, unmodified sources           (fidelity-only)
#   v1-workarounds  + tools/workarounds.py as land.py applies it
#   v2-fstype       + FSType 0
#   v3a-elweight    + TTFWeight 275, no rename   (ExtraLight x2)
#   v3b-el17        + LangName ID 17 [2] only    (ExtraLight x2)
#   v3c-elfull      + full rename                (ExtraLight x2)
#   v4-version      + version 1.002 edits        (Titillium x11)
# Run: bash investigations/next-fstype-verify/probes/run_all.sh  (after make_verify_inputs.sh)
set -uo pipefail
W=/home/fsanches/compartilhado/sfd-reland
V=$W/investigations/next-fstype-verify/runs
P=$W/investigations/next-fstype-verify/probes
S=/home/fsanches/compartilhado/sfd-reland-scratch/fstype-verify
BF0=/home/fsanches/compartilhado/babelfont-rs-worktrees/integration-ff-prs/target-heights/release/babelfont
export FAMILIES=$V/families-verify.tsv SCRATCH=$S
ALL=$(tail -n +2 $FAMILIES | cut -f7)
TW=$(echo "$ALL" | grep Titillium)
EL="TitilliumWeb-ExtraLight TitilliumWeb-ExtraLightItalic"
job() { # name bf set style
  local name=$1 bf=$2 set=$3 st=$4
  if [ "$set" = - ]; then
    BF=$bf OUT=$V/$name TAG=fstype-verify-$name bash $W/tools/baseline.sh $st
  else
    SRC_OVERRIDE=$S/$set/$st.sfd BF=$bf OUT=$V/$name TAG=fstype-verify-$name bash $W/tools/baseline.sh $st
  fi
}
export -f job; export W V S
{ for st in $ALL; do echo "v0-unmodified $BF0 - $st"; done
  for st in $ALL; do echo "v1-workarounds $P/bf_workarounds.sh - $st"; done
  for st in $ALL; do echo "v2-fstype $P/bf_workarounds.sh c-fstype $st"; done
  for st in $EL; do echo "v3a-elweight $P/bf_workarounds.sh c-elweight $st"; done
  for st in $EL; do echo "v3b-el17 $P/bf_workarounds.sh c-el17 $st"; done
  for st in $EL; do echo "v3c-elfull $P/bf_workarounds.sh c-elfull $st"; done
  for st in $TW; do echo "v4-version $P/bf_workarounds.sh c-version $st"; done
} | xargs -P 3 -L 1 bash -c 'job "$@"' _
