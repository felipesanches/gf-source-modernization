#!/bin/bash
# Question answered: babelfont's SFD reader ALREADY inserts an insertion marker into
# the abvm/blwm/kern/dist/mark/mkmk features it declares (fontforge.rs, Simon's
# 66334a7a: statements.insert(0, "# Automatic code start")), but fea-rs only honours a
# comment that starts with "# Automatic Code" (fea-rs 1.0.0 token_tree/typed.rs
# has_insert_marker, case-sensitive, after ufo2ft's INSERT_FEATURE_MARKER). Is the
# Lohit-Bengali mark-positioning loss the effect of that mis-cased marker, i.e. what
# does the build give when the converted .glyphs carries the marker fea-rs recognises?
#
# This is exactly what a one-line babelfont fix ("# Automatic code start" ->
# "# Automatic Code") would emit; it copies a finished harness run, rewrites the
# marker text only, rebuilds with gftools-builder3, gates, and counts rendering diffs.
#
# Usage: marker_case_fix.sh <harness scratch dir> <Style> <shipped.ttf> <OUT dir>
set -euo pipefail
src_run=$1; style=$2; shipped=$3; out=$4
B3=/home/fsanches/compartilhado/builder3-worktrees/main-e851b8b/target/release/gftools-builder
D3=/home/fsanches/compartilhado/diffenator3-venv/bin/diffenator3
PY=/home/fsanches/compartilhado/gftools/venv/bin/python3
TG=/home/fsanches/compartilhado/sfd-batch5/tools/table_gate.py
R=/home/fsanches/compartilhado/gf-source-modernization/investigations/next-provenance/probes/d3_render.py
d="$src_run-casefix"; rm -rf "$d"; mkdir -p "$d" "$out"
cp -a "$src_run/sources" "$d/"
n=$(grep -c '# Automatic code start' "$d/sources/$style.glyphs" || true)
sed -i 's/# Automatic code start/# Automatic Code/' "$d/sources/$style.glyphs"
echo "markers rewritten: $n" | tee "$out/$style.casefix.txt"
(cd "$d" && timeout 900 "$B3" sources/config.yaml) > "$out/$style.build.log" 2>&1
built=$(ls "$d"/fonts/ttf/*.ttf)
"$D3" -J 1 --no-languages --no-match --json --succinct "$shipped" "$built" > "$d/d3.json" 2>/dev/null
"$PY" "$TG" "$d/d3.json" --fonts "$shipped" "$built" > "$out/$style.gate.txt" 2>&1 || true
tail -1 "$out/$style.gate.txt" | tee -a "$out/$style.casefix.txt"
"$PY" "$R" "$d/d3.json" --list 5 | tee -a "$out/$style.casefix.txt"
