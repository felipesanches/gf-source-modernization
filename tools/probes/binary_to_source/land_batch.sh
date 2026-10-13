#!/bin/sh
# Lands binary-only families one at a time: for each family named, make_plan.py writes
# plans/<family>.json and its families-binary.tsv rows, both are committed (land.py refuses
# uncommitted evidence), then tools/land.py lands it. Prints "<family> <land.py verdict>".
# A family already in families-binary.tsv is skipped. Read each probe log first: only
# families whose probe was CLEAN and whose provenance is checked belong here.
#
#   BF_TREE=<babelfont tree> sh land_batch.sh <google/fonts> <repo archive> <log dir> <family>...
set -eu
GF=${1:?google/fonts}; ARCHIVE=${2:?repo archive}; L=${3:?log dir}; shift 3
EV=$(cd "$(dirname "$0")/../../.." && pwd)
PY=${PY:-python3}
mkdir -p "$L"
cd "$EV"
for f in "$@"; do
  if cut -f1 families-binary.tsv | grep -qx "$f"; then echo "$f already in families-binary.tsv"; continue; fi
  "$PY" tools/probes/binary_to_source/make_plan.py "$GF" upstream/main "$ARCHIVE" "$f" >> families-binary.tsv
  git add "plans/$f.json" families-binary.tsv
  git commit -q -m "families-binary: $f

Plan and rows from tools/probes/binary_to_source/make_plan.py; the probe was CLEAN.

Assisted by an AI agent (Claude Opus 5.5)"
  FAMILIES=families-binary.tsv SCRATCH="$L/scratch" "$PY" -u tools/land.py "$f" --unpublished-converter \
    < /dev/null > "$L/$f.log" 2>&1 || true
  echo "$f $(grep -m1 "^$f:" "$L/$f.log" | cut -d' ' -f2-)"
done
