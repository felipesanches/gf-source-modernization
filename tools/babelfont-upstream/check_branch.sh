#!/bin/sh
# Question: what are the fmt / clippy / test numbers a babelfont upstream PR body quotes,
# for the branch head and for its base (upstream/main)? Reproduces them from a clean
# copy of each tree, in its own cargo target dir (concurrent runs sharing one target dir
# picked up another branch's artifacts during review).
#
# Usage: sh check_branch.sh <branch> [base]      (base default: upstream/main)
#   e.g. sh check_branch.sh pr-ff-reader-fixes
# Prints, per tree: fmt clean?, clippy warnings (plain and --features cli), and the
# `cargo test -p babelfont --no-fail-fast` lib / integration / doc-test summary lines.
# The 11 lib failures on upstream/main 6ab2312 are pre-existing: 8 robocjk and 3
# decomposecomponentreferences tests load an untracked .rcjk fixture.
set -u
B=$1; BASE=${2:-upstream/main}
R=/home/fsanches/compartilhado/babelfont-rs-worktrees/gf-sfd-conversion   # any worktree of babelfont-rs
W=${W:-/home/fsanches/compartilhado/babelfont-rs-worktrees/check-branch-$(echo "$1" | tr / _)}   # on /home: two full cargo builds do not fit a tmpfs
for rev in "$BASE" "$B"; do
  tag=$(echo "$rev" | tr '/' '_')
  src="$W/src-$tag"; rm -rf "$src"; mkdir -p "$src"
  git -C "$R" archive "$rev" | tar -x -m -C "$src"          # -m: fresh mtimes, no stale cargo reuse
  export CARGO_TARGET_DIR="$W/target-$tag" CARGO_BUILD_JOBS=3
  sudo -n /usr/local/sbin/drop-caches >/dev/null 2>&1 || true
  echo "== $rev ($(git -C "$R" rev-parse --short "$rev"))"
  (cd "$src" && cargo fmt --all -- --check >/dev/null 2>&1) && echo "fmt: clean" || echo "fmt: NOT clean"
  for feat in "" "-p babelfont --features cli"; do
    # shellcheck disable=SC2086
    (cd "$src" && cargo clippy --all-targets $feat 2>&1) | grep -E '^warning' | sort | uniq -c > "$W/clippy-$tag.txt"
    echo "clippy ${feat:-(default)}: $(awk '{n+=$1} END{print n+0}' "$W/clippy-$tag.txt") warning line(s)"
    sed 's/^/    /' "$W/clippy-$tag.txt"
  done
  (cd "$src" && cargo test -p babelfont --no-fail-fast 2>&1) | grep -E '^test result' | sed 's/^/  /'
done
echo "workdir: $W"
