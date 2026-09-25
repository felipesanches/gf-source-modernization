#!/bin/sh
# Question: does the proposed --fontforge-legacy-offset-metrics filter close a style's
# vertical-metric rows when it runs where tools/recipe.py would put it -- FIRST, on the
# outlines exactly as the source states them (before --snap-component-transforms moves
# any component), which is what FontForge's exporter measured?
#
# tools/baseline.sh can only APPEND flags (EXTRA_FLAGS), and babelfont applies filters
# in command-line order. This wrapper is passed as BF=: it moves the flag, when present,
# to the front of the filter list and runs the prototype converter.
#
#   BF=<this file> EXTRA_FLAGS=--fontforge-legacy-offset-metrics \
#     FAMILIES=... OUT=... TAG=... SCRATCH=... bash tools/baseline.sh <Style>
#   PROTO=<babelfont binary> overrides the converter (default: the scratch prototype,
#   babelfont-rs integration-ff-prs 17ea899 + the filter; source diff in
#   ../runs/babelfont-proto.diff)
set -eu
PROTO=${PROTO:-/home/fsanches/compartilhado/sfd-reland-scratch/vmetrics/target/release/babelfont}
src=$1; out=$2; shift 2
first=""; rest=""
for a in "$@"; do
  if [ "$a" = --fontforge-legacy-offset-metrics ]; then first=$a; else rest="$rest $a"; fi
done
# shellcheck disable=SC2086
exec "$PROTO" "$src" "$out" $first $rest
