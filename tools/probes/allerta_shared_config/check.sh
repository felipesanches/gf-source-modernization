#!/bin/sh
# Question answered: googlefonts/allerta already holds Allerta (google/fonts pins bdd9557).
# The Allerta Stencil landing adds its source there and edits the shared sources/config.yaml.
# Does that change how Allerta Regular builds, and how close is each build to the shipped font?
#
# Usage: sh check.sh <landed allerta repo> <new commit> <google/fonts clone> <empty scratch dir>
# Builds Allerta-Regular.glyphs alone (the Stencil source dropped from the list) with each
# commit's config.yaml, using land.py's gftools-builder (B3=... to override).
set -eu
REPO=$1 NEW=$2 GF=$3 S=$4
B3=${B3:-/home/fsanches/compartilhado/tmp/gftools-rust-target/release/gftools-builder}
PY=${PY:-/home/fsanches/compartilhado/gftools/venv/bin/python3}
for rev in bdd9557 "$NEW"; do
  git clone -q "$REPO" "$S/$rev" && git -C "$S/$rev" checkout -q "$rev"
  sed -i '/AllertaStencil-Regular.glyphs/d' "$S/$rev/sources/config.yaml"
  (cd "$S/$rev" && "$B3" sources/config.yaml > build.log 2>&1)
done
"$PY" "$(dirname "$0")/compare.py" "$GF/ofl/allerta/Allerta-Regular.ttf" \
  "$S/bdd9557/fonts/ttf/Allerta-Regular.ttf" "$S/$NEW/fonts/ttf/Allerta-Regular.ttf"
