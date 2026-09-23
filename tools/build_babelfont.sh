#!/bin/sh
# Build the pinned converter and record exactly which commit it was built from.
#
# tools/land.py cites a babelfont revision in every convert commit, so the binary
# it runs must BE that revision: this refuses a worktree with uncommitted changes,
# builds, and writes the HEAD hash to target-heights/BUILT_FROM, which land.py
# compares against HEAD before converting anything.
#
# Usage: sh tools/build_babelfont.sh
set -eu
T=/home/fsanches/compartilhado/babelfont-rs-worktrees/gf-sfd-conversion
cd "$T"
if [ -n "$(git status --porcelain --untracked-files=no)" ]; then
  echo "refusing: $T has uncommitted changes" >&2; exit 1
fi
sudo -n /usr/local/sbin/drop-caches >/dev/null 2>&1 || true
CARGO_BUILD_JOBS=4 CARGO_TARGET_DIR="$T/target-heights" cargo build --release -q -p babelfont --features cli
git rev-parse HEAD > "$T/target-heights/BUILT_FROM"
echo "built $(git rev-parse --short HEAD) -> $T/target-heights/release/babelfont"
