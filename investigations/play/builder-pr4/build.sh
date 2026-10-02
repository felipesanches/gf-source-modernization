#!/bin/sh
# Question answered: what does gftools-builder (gftools-rust ade8776, the B3 that land.py
# cites) produce for Play when its glyphslib reads unquoted all-digit hex unicodes as hex,
# i.e. with glyphslib-rs PR #4 ("glyphs2: read an unquoted all-digit hex unicode as hex",
# felipesanches/glyphslib-rs fix-v2-unquoted-hex-unicode 27cb8bf, = v0.2.8 + that commit)?
#
# Builds that variant without touching any tracked file: a clone of gftools-rust at
# ade8776 and a Cargo [patch] given on the command line (--config).
#
# Usage: sh build.sh <scratch dir>        (needs ~2 GB; never /tmp)
#   -> <scratch>/target/release/gftools-builder ; run land.py with B3=<that path>
set -eu
S=$1
GR=${GR:-/home/fsanches/compartilhado/gftools-rust}
GL=${GL:-/home/fsanches/compartilhado/glyphslib-rs-worktrees/fix-v2-unquoted-hex-unicode}
test "$(git -C "$GL" rev-parse --short=7 HEAD)" = 27cb8bf
test -z "$(git -C "$GL" status --porcelain --untracked-files=no)"
mkdir -p "$S"
[ -d "$S/gftools-rust-pr4" ] || git clone -q "$GR" "$S/gftools-rust-pr4"
git -C "$S/gftools-rust-pr4" checkout -q ade8776
cd "$S/gftools-rust-pr4"
CARGO_BUILD_JOBS=${CARGO_BUILD_JOBS:-4} CARGO_TARGET_DIR="$S/target" \
  cargo build --release -p gftools-builder --config "patch.crates-io.glyphslib.path=\"$GL/glyphslib\""
grep -A2 '^name = "glyphslib"' Cargo.lock
echo "built: $S/target/release/gftools-builder"
