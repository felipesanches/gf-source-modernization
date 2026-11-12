#!/bin/sh
# Measurement landings (scratch only, never pushed) of the nine hinted binary-only families of
# reprobe-2026-11-12, on the hinting route A tools (tools/probes/hinting/ROUTE-A.md).
# Run from the gf-source-modernization root. Every path below is the caller's:
#   S        scratch directory (out/, scratch/, landed.tsv and one log per family go there)
#   BF_TREE  babelfont-rs checkout: main f1458803 merged with the branch typographic-family-names
#            (unpublished when this was written; PR-QUEUE 1c)
#   B3       gftools-builder built from the head of github.com/simoncozens/gftools-rust/pull/2
#   EXTRACT  gftools-extract-hinting from the head of github.com/googlefonts/gftools/pull/1248
#   PY       python with land.py's requirements
set -u
: "${S:?}" "${BF_TREE:?}" "${B3:?}" "${EXTRACT:?}" "${PY:?}"
L=tools/probes/binary_to_source/results/reprobe-2026-11-12/landing
for f in ubuntucondensed anonymouspro ekmukta kiranghaerang gothica1 gulim gulimche dotum dotumche; do
  OUT=$S/out LANDED=$S/landed.tsv SCRATCH=$S/scratch FAMILIES=$L/families.tsv PLANS=$L/plans \
  BF_TREE=$BF_TREE B3=$B3 HINTING_EXTRACT=$EXTRACT \
  "$PY" -u tools/land.py "$f" --unpublished-converter < /dev/null > "$S/$f.log" 2>&1
done
