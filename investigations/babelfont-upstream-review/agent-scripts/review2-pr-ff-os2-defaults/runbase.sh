#!/bin/bash
S=/tmp/claude-1000/-home-fsanches-compartilhado-GoogleFonts/f55394dc-b840-4055-b5b4-e2463e4b4dd8/scratchpad/review2-pr-ff-os2-defaults
export CARGO_TARGET_DIR=/home/fsanches/compartilhado/babelfont-rs-worktrees/target-review-pr-ff-os2-defaults/base
export CARGO_BUILD_JOBS=3
cd $S/base
cargo test -p babelfont --no-fail-fast > $S/test-base.log 2>&1; echo "base test rc=$?" >> $S/summary-base.txt
