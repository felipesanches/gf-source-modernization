#!/bin/bash
set -u
S=/tmp/claude-1000/-home-fsanches-compartilhado-GoogleFonts/f55394dc-b840-4055-b5b4-e2463e4b4dd8/scratchpad/review2-pr-ff-source-fidelity
W=/home/fsanches/compartilhado/babelfont-rs-worktrees/pr-ff-source-fidelity
T=/home/fsanches/compartilhado/babelfont-rs-worktrees/target-review-pr-ff-source-fidelity
export CARGO_BUILD_JOBS=3
while [ ! -f $S/head.done ]; do sleep 10; done
# base
rm -rf $S/base && mkdir -p $S/base
git -C $W archive upstream/main | tar -xm -C $S/base
( cd $S/base && CARGO_TARGET_DIR=$T/base cargo test -p babelfont --no-fail-fast > $S/test-base.log 2>&1; echo "test rc=$?" >> $S/test-base.log )
# per commit
: > $S/percommit.log
for c in $(git -C $W rev-list --reverse upstream/main..HEAD); do
  d=$S/pc-$c; rm -rf $d; mkdir -p $d
  git -C $W archive $c | tar -xm -C $d
  echo "=== $c $(git -C $W log -1 --format=%s $c)" >> $S/percommit.log
  ( cd $d
    cargo fmt --all -- --check >/dev/null 2>&1; echo "fmt rc=$?" >> $S/percommit.log
    CARGO_TARGET_DIR=$T/pc cargo clippy -p babelfont --all-targets --features cli > $d.clippy.log 2>&1; echo "clippy-cli rc=$? warnings=$(grep -c '^warning' $d.clippy.log)" >> $S/percommit.log
    CARGO_TARGET_DIR=$T/pc cargo clippy --all-targets > $d.clippy2.log 2>&1; echo "clippy rc=$? warnings=$(grep -c '^warning' $d.clippy2.log)" >> $S/percommit.log
    CARGO_TARGET_DIR=$T/pc cargo test -p babelfont --lib --no-fail-fast > $d.test.log 2>&1; echo "test: $(grep '^test result' $d.test.log | head -1)" >> $S/percommit.log
  )
done
echo DONE > $S/rest.done
