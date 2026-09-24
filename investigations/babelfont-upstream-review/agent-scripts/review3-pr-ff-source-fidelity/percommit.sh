#!/bin/bash
# Per-commit fmt + clippy on an exported tree (mtimes touched so cargo rebuilds changed files).
S=/tmp/claude-1000/-home-fsanches-compartilhado-GoogleFonts/f55394dc-b840-4055-b5b4-e2463e4b4dd8/scratchpad/review3-pr-ff-source-fidelity
R=/home/fsanches/compartilhado/babelfont-rs-worktrees/pr-ff-source-fidelity
X=/home/fsanches/compartilhado/babelfont-rs-worktrees/target-review3-pr-ff-source-fidelity/export
export CARGO_TARGET_DIR=/home/fsanches/compartilhado/babelfont-rs-worktrees/target-review3-pr-ff-source-fidelity CARGO_BUILD_JOBS=3
for c in $(git -C $R rev-list --reverse upstream/main..HEAD); do
  sudo -n /usr/local/sbin/drop-caches
  rm -rf $X; mkdir -p $X
  git -C $R archive $c | tar -x -m -C $X
  n=$(find $X -type f | wc -l); m=$(git -C $R ls-tree -r $c | wc -l)
  h=$(git -C $R rev-parse --short $c)
  (cd $X && cargo fmt --all -- --check >/dev/null 2>&1; echo "fmt=$?" ) > $S/pc-$h.txt
  echo "files=$n tree=$m" >> $S/pc-$h.txt
  (cd $X && cargo clippy -p babelfont --all-targets --features cli > $S/pc-$h-cli.log 2>&1; echo "cli_rc=$? warnings=$(grep -c '^warning' $S/pc-$h-cli.log)") >> $S/pc-$h.txt
  (cd $X && cargo clippy --all-targets --all-features -- -D warnings > $S/pc-$h-all.log 2>&1; echo "all_rc=$? warnings=$(grep -c '^warning\|^error' $S/pc-$h-all.log)") >> $S/pc-$h.txt
  (cd $X && cargo test -p babelfont --lib --no-fail-fast > $S/pc-$h-test.log 2>&1; echo "test: $(grep '^test result' $S/pc-$h-test.log)") >> $S/pc-$h.txt
done
echo done > $S/percommit.done
