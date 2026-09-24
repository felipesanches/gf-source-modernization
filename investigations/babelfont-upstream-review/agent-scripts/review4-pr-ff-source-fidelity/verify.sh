#!/bin/bash
S=/tmp/claude-1000/-home-fsanches-compartilhado-GoogleFonts/f55394dc-b840-4055-b5b4-e2463e4b4dd8/scratchpad/review4-pr-ff-source-fidelity
export CARGO_TARGET_DIR=/home/fsanches/compartilhado/babelfont-rs-worktrees/target-review4-pr-ff-source-fidelity
export CARGO_BUILD_JOBS=3
cd /home/fsanches/compartilhado/babelfont-rs-worktrees/pr-ff-source-fidelity
sudo -n /usr/local/sbin/drop-caches
cargo fmt --all -- --check > $S/fmt.log 2>&1; echo "fmt rc=$?" > $S/summary.txt
sudo -n /usr/local/sbin/drop-caches
cargo clippy --all-targets --all-features -- -D warnings > $S/clippy-all.log 2>&1; echo "clippy all-features rc=$?" >> $S/summary.txt
sudo -n /usr/local/sbin/drop-caches
cargo clippy -p babelfont --all-targets --features cli -- -D warnings > $S/clippy-cli.log 2>&1; echo "clippy cli rc=$?" >> $S/summary.txt
sudo -n /usr/local/sbin/drop-caches
cargo clippy --all-targets -- -D warnings > $S/clippy-default.log 2>&1; echo "clippy default rc=$?" >> $S/summary.txt
sudo -n /usr/local/sbin/drop-caches
cargo test -p babelfont --no-fail-fast > $S/test.log 2>&1; echo "test rc=$?" >> $S/summary.txt
sudo -n /usr/local/sbin/drop-caches
cargo build -p babelfont --features cli --bin babelfont > $S/build-cli.log 2>&1; echo "build cli rc=$?" >> $S/summary.txt
git status --porcelain > $S/status-after.txt
touch $S/done
