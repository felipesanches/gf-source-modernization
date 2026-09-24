#!/bin/bash
# Build and test HEAD with both companion branches applied on top (no repo writes).
S=/tmp/claude-1000/-home-fsanches-compartilhado-GoogleFonts/f55394dc-b840-4055-b5b4-e2463e4b4dd8/scratchpad/review3-pr-ff-source-fidelity
R=/home/fsanches/compartilhado/babelfont-rs-worktrees/pr-ff-source-fidelity
X=/home/fsanches/compartilhado/babelfont-rs-worktrees/target-review3-pr-ff-source-fidelity/export
export CARGO_TARGET_DIR=/home/fsanches/compartilhado/babelfont-rs-worktrees/target-review3-pr-ff-source-fidelity CARGO_BUILD_JOBS=3
sudo -n /usr/local/sbin/drop-caches
rm -rf $X; mkdir -p $X; git -C $R archive HEAD | tar -x -m -C $X
cd $X
for b in pr-ff-os2-defaults pr-ff-reader-fixes; do git -C $R diff upstream/main...$b | git apply -3 --index 2>/dev/null || git -C $R diff upstream/main...$b | git apply; echo "apply $b rc=$?"; done > $S/merged.log 2>&1
cargo fmt --all -- --check >> $S/merged.log 2>&1; echo "fmt rc=$?" >> $S/merged.log
cargo clippy --all-targets --all-features -- -D warnings > $S/merged-clippy.log 2>&1; echo "clippy rc=$?" >> $S/merged.log
cargo test -p babelfont --lib --no-fail-fast > $S/merged-test.log 2>&1; echo "test: $(grep '^test result' $S/merged-test.log)" >> $S/merged.log
echo done > $S/merged.done
