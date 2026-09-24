#!/bin/bash
# HEAD merged with pr-ff-os2-defaults (git merge-tree), then pr-ff-reader-fixes applied; build and test.
S=/tmp/claude-1000/-home-fsanches-compartilhado-GoogleFonts/f55394dc-b840-4055-b5b4-e2463e4b4dd8/scratchpad/review3-pr-ff-source-fidelity
R=/home/fsanches/compartilhado/babelfont-rs-worktrees/pr-ff-source-fidelity
X=/home/fsanches/compartilhado/babelfont-rs-worktrees/target-review3-pr-ff-source-fidelity/export
export CARGO_TARGET_DIR=/home/fsanches/compartilhado/babelfont-rs-worktrees/target-review3-pr-ff-source-fidelity CARGO_BUILD_JOBS=3
sudo -n /usr/local/sbin/drop-caches
T=$(git -C $R merge-tree --write-tree HEAD pr-ff-os2-defaults | head -1)
rm -rf $X; mkdir -p $X; git -C $R archive $T | tar -x -m -C $X
cd $X
{ git -C $R diff upstream/main...pr-ff-reader-fixes | git apply; echo "apply reader rc=$?"; } > $S/merged2.log 2>&1
cargo fmt --all -- --check >> $S/merged2.log 2>&1; echo "fmt rc=$?" >> $S/merged2.log
cargo clippy --all-targets --all-features -- -D warnings > $S/merged2-clippy.log 2>&1; echo "clippy rc=$?" >> $S/merged2.log
cargo test -p babelfont --lib --no-fail-fast > $S/merged2-test.log 2>&1; echo "test: $(grep '^test result' $S/merged2-test.log)" >> $S/merged2.log
cargo build -p babelfont --features cli --bin babelfont > /dev/null 2>&1 && ./../debug/babelfont --help 2>/dev/null | grep -E "^[A-Z].*:$" >> $S/merged2.log
$CARGO_TARGET_DIR/debug/babelfont --help 2>&1 | grep -cE "snap-component-transforms|drop-alternate-unicodes|keep-source-glyph-names" >> $S/merged2.log
echo done > $S/merged2.done
