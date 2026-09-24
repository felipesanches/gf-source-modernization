#!/bin/bash
set -u
S=/tmp/claude-1000/-home-fsanches-compartilhado-GoogleFonts/f55394dc-b840-4055-b5b4-e2463e4b4dd8/scratchpad/review2-pr-ff-source-fidelity
W=/home/fsanches/compartilhado/babelfont-rs-worktrees/pr-ff-source-fidelity
export CARGO_TARGET_DIR=/home/fsanches/compartilhado/babelfont-rs-worktrees/target-review-pr-ff-source-fidelity
export CARGO_BUILD_JOBS=3
cd $W
git rev-parse HEAD > $S/head.rev
cargo fmt --all -- --check > $S/fmt-head.log 2>&1; echo "fmt rc=$?" >> $S/fmt-head.log
cargo clippy --all-targets > $S/clippy-head.log 2>&1; echo "clippy rc=$?" >> $S/clippy-head.log
cargo clippy -p babelfont --all-targets --features cli > $S/clippy-cli-head.log 2>&1; echo "clippy-cli rc=$?" >> $S/clippy-cli-head.log
cargo test -p babelfont --no-fail-fast > $S/test-head.log 2>&1; echo "test rc=$?" >> $S/test-head.log
cargo build -p babelfont --features cli --bin babelfont > $S/build-cli-head.log 2>&1; echo "build rc=$?" >> $S/build-cli-head.log
git status --short > $S/status-after.log
echo DONE > $S/head.done
