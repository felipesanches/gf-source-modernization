#!/bin/bash
S=/tmp/claude-1000/-home-fsanches-compartilhado-GoogleFonts/f55394dc-b840-4055-b5b4-e2463e4b4dd8/scratchpad/review2-pr-ff-source-fidelity
W=/home/fsanches/compartilhado/babelfont-rs-worktrees/pr-ff-source-fidelity
T=/home/fsanches/compartilhado/babelfont-rs-worktrees/target-review-pr-ff-source-fidelity
export CARGO_BUILD_JOBS=3
until grep -q '^rc=' $S/doctest-base-rerun.log 2>/dev/null; do sleep 10; done
( cd $W && CARGO_TARGET_DIR=$T cargo clippy --all-targets --all-features -- -D warnings > $S/ci-clippy-head.log 2>&1; echo "rc=$?" >> $S/ci-clippy-head.log )
( cd $S/base && CARGO_TARGET_DIR=$T/base cargo clippy --all-targets --all-features -- -D warnings > $S/ci-clippy-base.log 2>&1; echo "rc=$?" >> $S/ci-clippy-base.log )
( cd $W && CARGO_TARGET_DIR=$T cargo test --workspace --no-fail-fast > $S/ci-test-head.log 2>&1; echo "rc=$?" >> $S/ci-test-head.log )
( cd $S/base && CARGO_TARGET_DIR=$T/base cargo test --workspace --no-fail-fast > $S/ci-test-base.log 2>&1; echo "rc=$?" >> $S/ci-test-base.log )
echo DONE > $S/ci.done
