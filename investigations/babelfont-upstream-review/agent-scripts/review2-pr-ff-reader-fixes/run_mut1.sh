#!/bin/bash
S=/tmp/claude-1000/-home-fsanches-compartilhado-GoogleFonts/f55394dc-b840-4055-b5b4-e2463e4b4dd8/scratchpad/review2-pr-ff-reader-fixes
export CARGO_TARGET_DIR=/home/fsanches/compartilhado/babelfont-rs-worktrees/target-review-pr-ff-reader-fixes
export CARGO_BUILD_JOBS=3
cd $S/mut
cargo test -p babelfont --lib convertors::fontforge::tests:: > $S/mut1-test.log 2>&1; echo "rc=$?" >> $S/mut1-test.log
