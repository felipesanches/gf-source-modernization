#!/bin/sh
# Question answered (DESIGN.md, Acceptance): with the TTF reader reading GPOS pair kerning into the
# master kerning, does every binary-route repository (families-binary.tsv) land as it does now --
# no style losing CLEAN, no shaping run differing?
# Converter: <BF_TREE> = branch 2026-11-02 + the kerning commit, built with tools/build_babelfont.sh.
# Usage: BF_TREE=<that worktree> sh tools/probes/ttf_gpos_kerning/accept.sh <scratch dir>
set -u
W=/home/fsanches/compartilhado/gf-source-modernization
S=${1:?scratch dir}
# LANDED= keeps these measurement rows out of landed.tsv, which push.sh reads
export FAMILIES=$W/families-binary.tsv OUT=$S/repos SCRATCH=$S/scratch LANDED=$S/landed.tsv TMPDIR=/home/fsanches/compartilhado/tmp
: "${BF_TREE:?BF_TREE}"
mkdir -p "$OUT" "$S/logs"
for repo in $(tail -n +2 "$FAMILIES" | cut -f1 | sort -u); do
    /home/fsanches/compartilhado/gftools/venv/bin/python3 -I "$W/tools/land.py" "$repo" --rebuild --unpublished-converter > "$S/logs/$repo.log" 2>&1
    grep -E "^$repo: " "$S/logs/$repo.log" | tail -1
done > "$S/logs/summary.txt"
echo done
