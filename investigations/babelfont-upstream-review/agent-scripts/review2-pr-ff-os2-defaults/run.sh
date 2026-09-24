#!/bin/bash
set -x
S=/tmp/claude-1000/-home-fsanches-compartilhado-GoogleFonts/f55394dc-b840-4055-b5b4-e2463e4b4dd8/scratchpad/review2-pr-ff-os2-defaults
export CARGO_TARGET_DIR=/home/fsanches/compartilhado/babelfont-rs-worktrees/target-review-pr-ff-os2-defaults
export CARGO_BUILD_JOBS=3
cd /home/fsanches/compartilhado/babelfont-rs-worktrees/pr-ff-os2-defaults
cargo fmt --all -- --check > $S/fmt.log 2>&1; echo "fmt rc=$?" >> $S/summary.txt
cargo clippy --all-targets > $S/clippy.log 2>&1; echo "clippy rc=$?" >> $S/summary.txt
cargo clippy -p babelfont --all-targets --features cli > $S/clippy-cli.log 2>&1; echo "clippy-cli rc=$?" >> $S/summary.txt
cargo test -p babelfont --no-fail-fast > $S/test.log 2>&1; echo "test rc=$?" >> $S/summary.txt
echo DONE >> $S/summary.txt
