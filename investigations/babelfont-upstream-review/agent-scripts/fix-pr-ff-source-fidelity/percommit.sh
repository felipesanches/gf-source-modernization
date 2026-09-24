#!/bin/bash
# Per-commit check: fmt, clippy (with and without cli), lib/integration/doc tests.
S=/tmp/claude-1000/-home-fsanches-compartilhado-GoogleFonts/f55394dc-b840-4055-b5b4-e2463e4b4dd8/scratchpad/fix-pr-ff-source-fidelity
R=/home/fsanches/compartilhado/babelfont-rs-worktrees/pr-ff-source-fidelity
export CARGO_TARGET_DIR=/home/fsanches/compartilhado/babelfont-rs-worktrees/target-prs-pr-ff-source-fidelity CARGO_BUILD_JOBS=3
OUT=$S/percommit.log; : > $OUT
for c in upstream/main $(git -C $R rev-list --reverse upstream/main..pr-ff-source-fidelity); do
  sha=$(git -C $R rev-parse --short $c)
  d=$S/pc/$sha; mkdir -p $d
  git -C $R archive $c | tar -xm -C $d
  cd $d
  fmt=$(cargo fmt --all -- --check >/dev/null 2>&1 && echo clean || echo DIRTY)
  c1=$(cargo clippy -p babelfont --all-targets --features cli 2>&1 | grep -cE '^(warning|error)')
  c2=$(cargo clippy --all-targets 2>&1 | grep -cE '^(warning|error)')
  t=$(cargo test -p babelfont --no-fail-fast 2>&1 | grep '^test result' | sed 's/; 0 measured.*//' | tr '\n' ' ')
  echo "$sha fmt=$fmt clippy_cli=$c1 clippy=$c2 tests: $t" >> $OUT
done
echo DONE >> $OUT
