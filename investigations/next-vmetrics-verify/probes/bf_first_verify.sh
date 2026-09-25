#!/bin/sh
# Question: does the proposed --fontforge-legacy-offset-metrics filter, rebuilt by the
# VERIFIER from the investigation's own diff (next-vmetrics/runs/babelfont-proto.diff on
# babelfont-rs integration-ff-prs 17ea899), close the rows when it runs FIRST (before
# --snap-component-transforms), as the proposed recipe.py change would pass it?
#
# Same job as next-vmetrics/probes/bf_first.sh, but pointing at the verifier's own build
# so the run does not depend on the investigation's binary.
#
#   BF=<this file> EXTRA_FLAGS=--fontforge-legacy-offset-metrics \
#     FAMILIES=... OUT=... TAG=... SCRATCH=... bash tools/baseline.sh <Style>
set -eu
PROTO=${PROTO:-/home/fsanches/compartilhado/sfd-reland-scratch/vmetrics-verify/target/release/babelfont}
src=$1; out=$2; shift 2
first=""; rest=""
for a in "$@"; do
  if [ "$a" = --fontforge-legacy-offset-metrics ]; then first=$a; else rest="$rest $a"; fi
done
# shellcheck disable=SC2086
exec "$PROTO" "$src" "$out" $first $rest
