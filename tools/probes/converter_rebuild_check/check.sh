#!/bin/sh
# Question answered: is the babelfont binary a landed repository cites (built by
# tools/build_babelfont.sh in its worktree's target-heights) really a build of that
# worktree's HEAD, and not a stale unit replayed from a target dir seeded from another
# worktree? Cargo gives a workspace member one unit hash in every worktree and judges
# freshness by mtime, so a seeded target dir can hand back another tree's binary.
#
# For each worktree: save the binary, `cargo clean -p babelfont`, rebuild, compare the
# sha256 (a release build is reproducible here); if it differed, the saved and the new
# binary would be compared on one font.
#   sh check.sh <scratch dir> <worktree>...
set -eu
S=${1:?scratch}; shift; mkdir -p "$S"
for W in "$@"; do
  b=$(basename "$W"); cp "$W/target-heights/release/babelfont" "$S/babelfont-$b-before"
  before=$(sha256sum "$S/babelfont-$b-before" | cut -c1-16)
  (cd "$W" && CARGO_TARGET_DIR="$W/target-heights" cargo clean -q -p babelfont)
  BF_TREE="$W" sh "$(dirname "$0")/../../build_babelfont.sh" >/dev/null 2>&1
  after=$(sha256sum "$W/target-heights/release/babelfont" | cut -c1-16)
  echo "$b ($(git -C "$W" rev-parse --short HEAD), BUILT_FROM $(cut -c1-8 "$W/target-heights/BUILT_FROM")): before $before after $after $([ "$before" = "$after" ] && echo IDENTICAL || echo DIFFERENT)"
done
