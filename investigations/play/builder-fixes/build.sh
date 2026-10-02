#!/bin/sh
# Question answered: what does gftools-builder produce for Play once the non-fontc tool
# fixes of 2026-10-02 are in, on top of the PR #4 variant (../builder-pr4/build.sh)?
#
#   gftools-rust ade8776 + static-autohint 1ce8f5f + instantiate-keep-instance 7f6eccd
#   glyphslib-rs 27cb8bf (PR #4) + fix-v2-master-name-omitted-weight ed4fc2a
#
# Builds in clones under <scratch>; no tracked file anywhere changes.
#
# Usage: sh build.sh <scratch dir>        (needs ~3 GB; never /tmp)
#   -> <scratch>/target/release/gftools-builder ; run land.py with B3=<that path>
set -eu
S=$1
GR=${GR:-/home/fsanches/compartilhado/gftools-rust}
GL=${GL:-/home/fsanches/compartilhado/glyphslib-rs}
mkdir -p "$S"
[ -d "$S/gftools-rust" ] || git clone -q "$GR" "$S/gftools-rust"
git -C "$S/gftools-rust" checkout -q -B measure ade8776
git -C "$S/gftools-rust" -c user.name=measure -c user.email=measure@localhost \
  cherry-pick 1ce8f5f 7f6eccd
[ -d "$S/glyphslib-rs" ] || git clone -q "$GL" "$S/glyphslib-rs"
git -C "$S/glyphslib-rs" checkout -q -B measure 27cb8bf
git -C "$S/glyphslib-rs" -c user.name=measure -c user.email=measure@localhost \
  cherry-pick ed4fc2a
cd "$S/gftools-rust"
CARGO_BUILD_JOBS=${CARGO_BUILD_JOBS:-4} CARGO_TARGET_DIR="$S/target" \
  cargo build --release -p gftools-builder \
  --config "patch.crates-io.glyphslib.path=\"$S/glyphslib-rs/glyphslib\""
grep -A2 '^name = "glyphslib"' Cargo.lock
git log --oneline -3
echo "built: $S/target/release/gftools-builder"
