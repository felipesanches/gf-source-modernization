#!/bin/sh
# Question answered: what does moving fontc_crater's gftools pin from A to B change, all else
# equal? Runs `fontc_crater ci` on <subset.json> twice -- once with <venv A>, once with
# <venv B> -- from the same fontc checkout and binaries, each with crater's cached results
# cleared (crater reuses them when only Python tools change), then compare.py on the two.
#
#   sh run_pair.sh <fontc checkout> <venv A> <venv B> <subset.json> <scratch dir>
#
# <fontc checkout>/target must hold release builds of fontc_crater, fontc and otl-normalizer
# (crater looks for them in <cwd>/target/release); crater also runs `cargo build` there itself,
# so a toolchain the checkout needs must be the active one (RUSTUP_TOOLCHAIN=1.97.1 for fontc
# 6bbfa26d). Writes <scratch>/out-A, out-B, their logs and compare.txt.
#
# <scratch>/cache may be a symlink to an existing crater cache (saves the clones); it is
# resolved first, because ttx_diff (fontc 6bbfa26d) resolves the config path but not the source
# path, so through a symlink every gftools-mode target gets a wrong --experimental-single-source
# and gftools rejects it ("must match exactly one of ... (matched 0)").
set -eu
FONTC=${1:?fontc checkout}; VA=${2:?venv A}; VB=${3:?venv B}; SUBSET=${4:?subset.json}; S=${5:?scratch dir}
HERE=$(cd "$(dirname "$0")" && pwd)
mkdir -p "$S/cache"
CACHE=$(cd "$S/cache" && pwd -P)
for side in A B; do
  if [ $side = A ]; then venv=$VA; else venv=$VB; fi
  rm -rf -- "${CACHE:?}/crater_cached_results" "${S:?}/out-${side:?}"
  mkdir -p "$S/out-$side"
  ( cd "$FONTC" && PATH="$venv/bin:$PATH" ./target/release/fontc_crater ci "$SUBSET" \
      --cache "$CACHE" --out "$S/out-$side" ) > "$S/out-$side.log" 2>&1 || true
  echo "$side done"
done
RA=$(ls -t "$S"/out-A/[0-9]*.json | head -1)
RB=$(ls -t "$S"/out-B/[0-9]*.json | head -1)
python3 "$HERE/compare.py" "$RA" "$RB" | tee "$S/compare.txt"
