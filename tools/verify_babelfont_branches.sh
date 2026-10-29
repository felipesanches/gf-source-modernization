#!/bin/sh
# Verify babelfont-rs branches one worktree at a time in one clean cargo target.
#
# Question answered: does each branch, as it stands, pass CI's gates (cargo fmt --check,
# cargo clippy --all-targets, cargo test) on its own, with no build artefact replayed
# from another worktree? (Workspace members share a unit hash across worktrees and
# cargo's freshness is by mtime, so a shared target without `cargo clean -p babelfont`
# reports another branch's result: 2026-10-24, twelve branches "passed 282 tests".)
#
# Usage: sh tools/verify_babelfont_branches.sh <tag> <worktree>...
#   -> logs/babelfont-verify-<tag>/<worktree>.log and summary.tsv
#      (worktree, head, fmt, clippy, tests: "N passed; M failed" or FAIL)
set -u
TAG=${1:?tag}; shift
W=/home/fsanches/compartilhado/babelfont-rs-worktrees
OUT=/home/fsanches/compartilhado/gf-source-modernization/logs/babelfont-verify-$TAG
mkdir -p "$OUT"
export RUSTUP_TOOLCHAIN=1.97.1 CARGO_BUILD_JOBS=4
export CARGO_TARGET_DIR=/home/fsanches/compartilhado/tmp/pr-check-target
export TMPDIR=/home/fsanches/compartilhado/tmp
printf 'worktree\thead\tfmt\tclippy\ttests\n' > "$OUT/summary.tsv"
for wt in "$@"; do
    d=$W/$wt; log=$OUT/$wt.log; head=$(git -C "$d" rev-parse --short=8 HEAD)
    { echo "== $wt $head $(date -u +%FT%TZ)"
      (cd "$d" && cargo clean -p babelfont -p sr-aef 2>&1 | tail -1)
      (cd "$d" && cargo fmt --all -- --check >/dev/null 2>&1) && fmt=ok || fmt=FAIL
      echo "fmt: $fmt"
      (cd "$d" && cargo clippy --all-targets 2>&1 | tail -3 | grep -q 'warning\|error' ) && clippy=WARN || clippy=ok
      echo "clippy: $clippy"
      (cd "$d" && cargo test --no-fail-fast 2>&1 | grep -E '^test result|FAILED|panicked' ) 
    } > "$log" 2>&1
    tests=$(awk '/^test result/{p+=$4; f+=$6} END{printf "%d passed; %d failed", p, f}' "$log")
    printf '%s\t%s\t%s\t%s\t%s\n' "$wt" "$head" "$(grep -m1 '^fmt:' "$log" | cut -d' ' -f2)" "$(grep -m1 '^clippy:' "$log" | cut -d' ' -f2)" "$tests" >> "$OUT/summary.tsv"
done
echo "done: $OUT/summary.tsv"
