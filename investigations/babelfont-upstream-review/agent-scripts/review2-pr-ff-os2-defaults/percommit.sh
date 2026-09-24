#!/bin/bash
S=/tmp/claude-1000/-home-fsanches-compartilhado-GoogleFonts/f55394dc-b840-4055-b5b4-e2463e4b4dd8/scratchpad/review2-pr-ff-os2-defaults
T=/home/fsanches/compartilhado/babelfont-rs-worktrees/target-review-pr-ff-os2-defaults
W=/home/fsanches/compartilhado/babelfont-rs-worktrees/pr-ff-os2-defaults
export TMPDIR=$T/tmp CARGO_TARGET_DIR=$T/percommit CARGO_BUILD_JOBS=3
: > $S/percommit.txt
for c in $(git -C $W rev-list --reverse upstream/main..HEAD); do
  rm -rf $T/pc-src; mkdir -p $T/pc-src
  git -C $W archive $c | tar -x -m -C $T/pc-src
  cd $T/pc-src
  cargo fmt --all -- --check > $S/pc-$c-fmt.log 2>&1; f=$?
  cargo clippy --all-targets > $S/pc-$c-clippy.log 2>&1; c1=$?; w1=$(grep -c '^warning' $S/pc-$c-clippy.log)
  cargo clippy -p babelfont --all-targets --features cli > $S/pc-$c-clippycli.log 2>&1; c2=$?; w2=$(grep -c '^warning' $S/pc-$c-clippycli.log)
  cargo test -p babelfont --lib --no-fail-fast > $S/pc-$c-test.log 2>&1
  r=$(grep '^test result' $S/pc-$c-test.log)
  echo "$c fmt=$f clippy=$c1/$w1 clippycli=$c2/$w2 $r" >> $S/percommit.txt
  cd /
done
echo DONE >> $S/percommit.txt
