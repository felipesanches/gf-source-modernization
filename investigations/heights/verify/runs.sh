#!/bin/bash
# Sequential harness runs for the heights verification (one build at a time).
set -u
# V: a working directory for run outputs (regenerable). The edited sources this
# verifier made were byte-identical to the investigation's ../edits/, which are
# read from there.
V=${V:-$(mktemp -d)}
EDITS=$(cd "$(dirname "$0")/../edits" && pwd)
W=/home/fsanches/compartilhado/sfd-reland
BFH=/home/fsanches/compartilhado/babelfont-rs-worktrees/gf-sfd-conversion/target-heights/release/babelfont
export SCRATCH=$V/harness
run() { # name style [override] ; BF from env
  TAG=heights-verify OUT=$V/runs/$1 SRC_OVERRIDE="${3:-}" bash $W/tools/baseline.sh "$2"
}
declare -A E=([HerrVonMuellerhoff-Regular]=HerrVonMuellerhoff-2011rule [Miama-Regular]=Miama-2011rule [NosiferCaps-Regular]=NosiferCaps-2011rule [PatrickHand-Regular]=PatrickHand-capheight661 [UnifrakturCook-Bold]=UnifrakturCook-2011rule)
for s in HerrVonMuellerhoff-Regular Miama-Regular NosiferCaps-Regular PatrickHand-Regular UnifrakturCook-Bold; do
  BF=$BFH run after-ca43adc "$s" "$EDITS/${E[$s]}.sfd"
done
for s in HerrVonMuellerhoff-Regular Miama-Regular NosiferCaps-Regular PatrickHand-Regular UnifrakturCook-Bold; do
  BF=$BFH run before-ca43adc "$s"
done
run pinned-edit PatrickHand-Regular "$EDITS/PatrickHand-capheight661.sfd"
echo ALL-RUNS-DONE
