#!/bin/bash
# Sequential harness runs for the heights verification (one build at a time).
set -u
V=/tmp/claude-1000/-home-fsanches-compartilhado-GoogleFonts/f55394dc-b840-4055-b5b4-e2463e4b4dd8/scratchpad/inv-heights-verify
W=/home/fsanches/compartilhado/sfd-reland
BFH=/home/fsanches/compartilhado/babelfont-rs-worktrees/gf-sfd-conversion/target-heights/release/babelfont
export SCRATCH=$V/harness
run() { # name style [override] ; BF from env
  TAG=heights-verify OUT=$V/runs/$1 SRC_OVERRIDE="${3:-}" bash $W/tools/baseline.sh "$2"
}
declare -A E=([HerrVonMuellerhoff-Regular]=HerrVonMuellerhoff-Regular-TTF [Miama-Regular]=Miama-Regular-TTF [NosiferCaps-Regular]=NosiferCaps-Regular-TTF [PatrickHand-Regular]=PatrickHand-Regular-TTF [UnifrakturCook-Bold]=UnifrakturCook-Bold-TTF)
for s in HerrVonMuellerhoff-Regular Miama-Regular NosiferCaps-Regular PatrickHand-Regular UnifrakturCook-Bold; do
  BF=$BFH run after-ca43adc "$s" "$V/edits/${E[$s]}.sfd"
done
for s in HerrVonMuellerhoff-Regular Miama-Regular NosiferCaps-Regular PatrickHand-Regular UnifrakturCook-Bold; do
  BF=$BFH run before-ca43adc "$s"
done
run pinned-edit PatrickHand-Regular "$V/edits/PatrickHand-Regular-TTF.sfd"
echo ALL-RUNS-DONE
