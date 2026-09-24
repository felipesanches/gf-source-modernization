#!/bin/sh
# Per-commit gate for pr-ff-os2-defaults on 496e904: each commit alone must pass
# fmt, clippy (default and -p babelfont --features cli) and cargo test -p babelfont
# with only the 11 pre-existing .rcjk-fixture failures.
set -u
R=/home/fsanches/compartilhado/babelfont-rs-worktrees/pr-ff-os2-defaults
W=/home/fsanches/compartilhado/babelfont-rs-worktrees/port-496e904-work/review-pr-ff-os2-defaults/percommit
mkdir -p "$W"
export CARGO_TARGET_DIR="$W/target" CARGO_BUILD_JOBS=3
for c in $(git -C "$R" rev-list --reverse 496e904..119f2be); do
  s=$(git -C "$R" rev-parse --short "$c"); src="$W/src-$s"; rm -rf "$src"; mkdir -p "$src"
  git -C "$R" archive "$c" | tar -x -m -C "$src"
  echo "== $s $(git -C "$R" log -1 --format=%s "$c")"
  (cd "$src" && cargo fmt --all -- --check >/dev/null 2>&1) && echo "fmt: clean" || echo "fmt: NOT clean"
  for feat in "" "-p babelfont --features cli"; do
    n=$( (cd "$src" && cargo clippy --all-targets $feat 2>&1) | tee "$W/clippy-$s-${feat:+cli}.log" | grep -cE '^(warning|error)')
    echo "clippy ${feat:-(default)}: $n warning/error line(s)"
  done
  (cd "$src" && cargo test -p babelfont --no-fail-fast 2>&1) > "$W/test-$s.log"
  grep -E '^test result' "$W/test-$s.log" | sed 's/^/  /'
  echo "  failed: $(grep -E '^test .* FAILED$' "$W/test-$s.log" | awk '{print $2}' | sort | tr '\n' ' ')"
  rm -rf "$src"
done
