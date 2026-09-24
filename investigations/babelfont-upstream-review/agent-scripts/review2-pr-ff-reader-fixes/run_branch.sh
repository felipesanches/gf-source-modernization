#!/bin/bash
S=/tmp/claude-1000/-home-fsanches-compartilhado-GoogleFonts/f55394dc-b840-4055-b5b4-e2463e4b4dd8/scratchpad/review2-pr-ff-reader-fixes
export CARGO_TARGET_DIR=/home/fsanches/compartilhado/babelfont-rs-worktrees/target-review-pr-ff-reader-fixes
export CARGO_BUILD_JOBS=3
cd /home/fsanches/compartilhado/babelfont-rs-worktrees/pr-ff-reader-fixes
cargo fmt --all -- --check > $S/branch-fmt.log 2>&1; echo "fmt rc=$?" >> $S/branch-fmt.log
cargo clippy --all-targets > $S/branch-clippy.log 2>&1; echo "clippy rc=$?" >> $S/branch-clippy.log
cargo clippy -p babelfont --all-targets --features cli > $S/branch-clippy-cli.log 2>&1; echo "clippy-cli rc=$?" >> $S/branch-clippy-cli.log
cargo test -p babelfont --no-fail-fast > $S/branch-test.log 2>&1; echo "test rc=$?" >> $S/branch-test.log
echo DONE > $S/branch.done
