#!/bin/sh
# Base test counts on upstream/main, then a CLI smoke test of the snap filter (disposable).
set -u
REPO=/home/fsanches/compartilhado/babelfont-rs-worktrees/pr-ff-source-fidelity
S=/tmp/claude-1000/-home-fsanches-compartilhado-GoogleFonts/f55394dc-b840-4055-b5b4-e2463e4b4dd8/scratchpad/fix3-pr-ff-source-fidelity
export CARGO_TARGET_DIR=/home/fsanches/compartilhado/babelfont-rs-worktrees/target-prs-pr-ff-source-fidelity
export CARGO_BUILD_JOBS=3
export TMPDIR=$CARGO_TARGET_DIR/tmp
W=$TMPDIR/base
rm -rf $W; mkdir -p $W
git -C $REPO archive upstream/main | tar -xm -C $W
cd $W && cargo test -p babelfont --no-fail-fast 2>&1 | grep -E '^test result|^    [a-z_:]+$' | sed 's/^/base: /'
cd / && rm -rf $W
cd $REPO && cargo build -q -p babelfont --features cli --bin babelfont 2>&1 | tail -3
B=$CARGO_TARGET_DIR/debug/babelfont
TTX=/home/fsanches/compartilhado/gftools/venv/bin/ttx
for mode in plain snap; do
  flag=""; [ $mode = snap ] && flag=--snap-component-transforms
  $B $S/mixed.sfd $TMPDIR/mixed-$mode.ttf $flag >/dev/null 2>&1; echo "$mode rc=$?"
  $TTX -q -t glyf -o - $TMPDIR/mixed-$mode.ttf 2>/dev/null | grep -E '<TTGlyph|<pt |<component' | sed "s/^/$mode: /"
done
