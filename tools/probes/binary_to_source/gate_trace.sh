#!/bin/sh
# Question answered: for each style of a probe_batch.sh run, why does the table gate's GSUB
# lookup-order arbitration refuse (tools/table_gate.py with GATE_TRACE=1), and which rows
# still block? Re-runs only the table gate, on the run's diffenator3 JSON and built font.
#
#   PY=<python with fontTools, uharfbuzz> sh gate_trace.sh <google/fonts> <probe_batch scratch>
#
# Prints, per style: the release stem, the TRACE lines and the BLOCKING rows (cut to 160 chars).
set -eu
GF=${1:?google/fonts checkout}; S=${2:?probe_batch.sh scratch dir}
HERE=$(cd "$(dirname "$0")" && pwd)
PY=${PY:-python3}
cut -f1 "$S/summary.tsv" | while read -r f; do
  for sd in "$S/$f"/*/; do
    stem=$(basename "$sd")
    rel=$(ls "$GF"/ofl/"$f"/"$stem".ttf "$GF"/apache/"$f"/"$stem".ttf "$GF"/ufl/"$f"/"$stem".ttf 2>/dev/null | head -1)
    built=$(ls "$sd"fonts/ttf/*.ttf 2>/dev/null | head -1)
    json=$(ls "$sd"*.d3.json 2>/dev/null | head -1)
    echo "== $f $stem"
    if [ -z "$rel" ] || [ -z "$built" ] || [ -z "$json" ]; then
      echo "   (no release, build or diffenator3 JSON)"; continue
    fi
    GATE_TRACE=1 "$PY" "$HERE/../../table_gate.py" "$json" --fonts "$rel" "$built" 2>&1 \
      | grep -E '^(TRACE|BLOCKING|   release=|   ours   =)' | cut -c1-160 | sed 's/^/   /'
  done
done
