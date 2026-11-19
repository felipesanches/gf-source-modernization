#!/bin/sh
# Question: do the eight HanYang families google/fonts takes from googlefonts/batang (Batang,
# BatangChe, Gungsuh, GungsuhChe) and googlefonts/gulim (Gulim, GulimChe, Dotum, DotumChe)
# rebuild from sources converted from their shipped binaries (no outline source exists: the
# repos run vendor TTFs through process.py)?
# Inputs: the shipped TTFs at google/fonts $REF, probe.py of gf-source-modernization,
# babelfont 2026-11-02 (26fdcfa9), gftools-builder land.py B3_DEFAULT.
# Usage: sh tools/probes/hanyang_from_binary/run_probe.sh <scratch dir> [family...]
set -eu
W=${1:?scratch dir}; shift
FAMS=${*:-batang batangche gungsuh gungsuhche gulim gulimche dotum dotumche}
REF=${REF:-HEAD}
GFR=/home/fsanches/compartilhado/gfonts
GSM=/home/fsanches/compartilhado/gf-source-modernization
mkdir -p "$W/shipped"
git -C "$GFR" rev-parse "$REF" > "$W/google-fonts-ref.txt"
for f in $FAMS; do
  git -C "$GFR" archive "$REF" "ofl/$f" | tar -x -C "$W/shipped" --wildcards '*.ttf'
done
export BF=/home/fsanches/compartilhado/babelfont-rs-worktrees/2026-11-02/target-heights/release/babelfont
git -C /home/fsanches/compartilhado/babelfont-rs-worktrees/2026-11-02 rev-parse HEAD > "$W/babelfont-rev.txt"
for f in $FAMS; do
  /home/fsanches/compartilhado/gftools/venv/bin/python3 -I "$GSM/tools/probes/binary_to_source/probe.py" "$W/work" "$W"/shipped/ofl/$f/*.ttf
done
