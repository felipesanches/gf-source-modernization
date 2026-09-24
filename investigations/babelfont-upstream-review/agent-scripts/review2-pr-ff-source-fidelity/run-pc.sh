#!/bin/bash
S=/tmp/claude-1000/-home-fsanches-compartilhado-GoogleFonts/f55394dc-b840-4055-b5b4-e2463e4b4dd8/scratchpad/review2-pr-ff-source-fidelity
W=/home/fsanches/compartilhado/babelfont-rs-worktrees/pr-ff-source-fidelity
T=/home/fsanches/compartilhado/babelfont-rs-worktrees/target-review-pr-ff-source-fidelity
export CARGO_BUILD_JOBS=3
until [ -f $S/ci.done ]; do sleep 10; done
: > $S/percommit2.log
for c in $(git -C $W rev-list --reverse upstream/main..HEAD); do
  d=$S/pc; rm -rf $d; mkdir -p $d
  git -C $W archive $c | tar -xm -C $d || { echo "extract failed $c" >> $S/percommit2.log; continue; }
  echo "=== $c $(git -C $W log -1 --format=%s $c) files=$(find $d -type f | wc -l) expected=$(git -C $W ls-tree -r $c | wc -l)" >> $S/percommit2.log
  ( cd $d
    cargo fmt --all -- --check >/dev/null 2>&1; echo "fmt rc=$?" >> $S/percommit2.log
    CARGO_TARGET_DIR=$T/pc cargo clippy -p babelfont --all-targets --features cli > $S/pc.clippy.log 2>&1; echo "clippy-cli rc=$? warnings=$(grep -c '^warning' $S/pc.clippy.log)" >> $S/percommit2.log
    CARGO_TARGET_DIR=$T/pc cargo clippy --all-targets --all-features -- -D warnings > $S/pc.clippy2.log 2>&1; echo "clippy-all-features -D warnings rc=$? warnings=$(grep -c '^warning\|^error' $S/pc.clippy2.log)" >> $S/percommit2.log
    CARGO_TARGET_DIR=$T/pc cargo test -p babelfont --lib --no-fail-fast > $S/pc.test.log 2>&1; echo "test: $(grep '^test result' $S/pc.test.log | head -1)" >> $S/percommit2.log
  )
  rm -rf $d
done
echo DONE > $S/pc.done
