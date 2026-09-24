#!/bin/sh
# Question: does each filter change a converted font the same way before the port
# (4a293d4 on 0b55947) and after it (119f2be on 496e904)? For every SFD and filter
# set, the flattened JSON delta (filtered .babelfont minus unfiltered .babelfont) of
# the pre-port binary must equal that of the post-port binary. Upstream reader changes
# (e.g. #85 win/hhea) show up only in the unfiltered comparison, reported separately.
set -u
R=/home/fsanches/compartilhado/babelfont-rs-worktrees/pr-ff-os2-defaults
W=/home/fsanches/compartilhado/babelfont-rs-worktrees/port-496e904-work/review-pr-ff-os2-defaults/probe
mkdir -p "$W"
for rev in 4a293d4 119f2be; do
  src="$W/src-$rev"
  if [ ! -x "$W/target-$rev/debug/babelfont" ]; then
    rm -rf "$src"; mkdir -p "$src"; git -C "$R" archive "$rev" | tar -x -m -C "$src"
    (cd "$src" && CARGO_TARGET_DIR="$W/target-$rev" CARGO_BUILD_JOBS=3 cargo build -q -p babelfont --features cli --bin babelfont) || { echo "build $rev failed"; exit 1; }
  fi
done
python3 "$(dirname "$0")/probe_cmp.py" "$W" "$@"
