#!/bin/sh
# Question: do the 17 googlefontdirectory-hg families of google/fonts#10589 (googlefonts/<fam> =
# librefonts forks holding -TTF.sfd imports) land CLEAN from their shipped binaries (P13)?
# Inputs: the shipped TTFs at google/fonts main (REF), extracted to $W/shipped; probe.py of
# gf-source-modernization, babelfont 2026-11-02 (26fdcfa9), gftools-builder land.py B3_DEFAULT.
# Usage: sh tools/probes/hg_forks_from_binary/run_probe.sh <scratch dir>   (VARIABLE unset: static build)
set -eu
W=${1:?scratch dir}
REF=${REF:-refs/remotes/upstream-gf/main}
GFR=/home/fsanches/compartilhado/google/fonts
GSM=/home/fsanches/compartilhado/gf-source-modernization
FAMS="kronaone oldenburg ovo passeroone pollerone pompiere rye sarina shortstack snowburstone sonsieone spinnaker stoke supermercadoone tauri vastshadow wellfleet"
mkdir -p "$W/shipped"
git -C "$GFR" rev-parse "$REF" > "$W/google-fonts-ref.txt"
for f in $FAMS; do
  git -C "$GFR" archive "$REF" "ofl/$f" | tar -x -C "$W/shipped" --wildcards '*.ttf'
done
export BF=/home/fsanches/compartilhado/babelfont-rs-worktrees/2026-11-02/target-heights/release/babelfont
git -C /home/fsanches/compartilhado/babelfont-rs-worktrees/2026-11-02 rev-parse HEAD > "$W/babelfont-rev.txt"
/home/fsanches/compartilhado/gftools/venv/bin/python3 -I "$GSM/tools/probes/binary_to_source/probe.py" "$W/work" $(ls "$W"/shipped/ofl/*/*.ttf)
