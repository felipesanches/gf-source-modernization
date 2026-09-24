#!/bin/bash
S=/tmp/claude-1000/-home-fsanches-compartilhado-GoogleFonts/f55394dc-b840-4055-b5b4-e2463e4b4dd8/scratchpad/review2-pr-ff-source-fidelity
W=/home/fsanches/compartilhado/babelfont-rs-worktrees/pr-ff-source-fidelity
T=/home/fsanches/compartilhado/babelfont-rs-worktrees/target-review-pr-ff-source-fidelity
export CARGO_BUILD_JOBS=3
while [ ! -f $S/rest.done ]; do sleep 10; done
( cd $W && CARGO_TARGET_DIR=$T cargo doc -p babelfont --no-deps > $S/doc-head.log 2>&1; echo "doc rc=$?" >> $S/doc-head.log )
( cd $S/base && CARGO_TARGET_DIR=$T/base cargo doc -p babelfont --no-deps > $S/doc-base.log 2>&1; echo "doc rc=$?" >> $S/doc-base.log )
echo DONE > $S/doc.done
