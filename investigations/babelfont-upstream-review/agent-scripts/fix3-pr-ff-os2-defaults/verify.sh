#!/bin/sh
# Per-commit fmt/clippy/lib-test check of pr-ff-os2-defaults.
set -u
W=/home/fsanches/compartilhado/babelfont-rs-worktrees/pr-ff-os2-defaults
export CARGO_TARGET_DIR=/home/fsanches/compartilhado/babelfont-rs-worktrees/target-prs-pr-ff-os2-defaults
export CARGO_BUILD_JOBS=3
export TMPDIR=$CARGO_TARGET_DIR/tmp
mkdir -p "$TMPDIR"
cd "$W" || exit 1
for c in $(git rev-list --reverse upstream/main..pr-ff-os2-defaults); do
  git checkout -q --detach "$c" || exit 1
  echo "=== $(git log -1 --format='%h %s')"
  cargo fmt --all -- --check >/dev/null 2>&1 && echo "fmt: clean" || echo "fmt: DIRTY"
  echo "clippy: $(cargo clippy --all-targets 2>&1 | grep -c '^warning\|^error') warning/error lines"
  echo "clippy cli: $(cargo clippy -p babelfont --all-targets --features cli 2>&1 | grep -c '^warning\|^error') warning/error lines"
  cargo test -p babelfont --lib --no-fail-fast 2>&1 | grep -E '^test result'
done
git checkout -q pr-ff-os2-defaults
