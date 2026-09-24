#!/bin/sh
# Per-commit fmt/clippy/test check of pr-ff-source-fidelity (disposable).
set -u
REPO=/home/fsanches/compartilhado/babelfont-rs-worktrees/pr-ff-source-fidelity
export CARGO_TARGET_DIR=/home/fsanches/compartilhado/babelfont-rs-worktrees/target-prs-pr-ff-source-fidelity
export CARGO_BUILD_JOBS=3
export TMPDIR=$CARGO_TARGET_DIR/tmp
W=$TMPDIR/percommit
for c in $(git -C $REPO rev-list --reverse upstream/main..HEAD); do
  rm -rf $W; mkdir -p $W
  git -C $REPO archive $c | tar -xm -C $W
  n=$(find $W -type f | wc -l); t=$(git -C $REPO ls-tree -r $c | wc -l)
  cd $W
  cargo fmt --all -- --check >/dev/null 2>&1; f=$?
  c1=$(cargo clippy -p babelfont --all-targets --features cli 2>&1 | grep -cE '^(warning|error)')
  cargo clippy --all-targets --all-features -- -D warnings >/dev/null 2>&1; c2=$?
  r=$(cargo test -p babelfont --lib --no-fail-fast 2>&1 | grep '^test result')
  echo "$(git -C $REPO log -1 --format='%h %s' $c) | files $n/$t fmt=$f clippy_cli=$c1 clippy_allfeat_rc=$c2 | $r"
  cd /
done
rm -rf $W
