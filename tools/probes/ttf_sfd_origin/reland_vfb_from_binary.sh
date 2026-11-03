#!/bin/sh
# Question answered: do the VFB families whose .vfb is a FontLab import of the shipped binary
# ("-TTF"/"-OTF" .vfb in families-vfb.tsv; Simon on google/fonts#10490) land CLEAN when converted
# from the shipped binaries themselves with babelfont's TTF reader, without the VFB branches?
# Converter: felipesanches/babelfont-rs branch 2026-11-02 (26fdcfa9, public), the one the 16
# binary families of PR-QUEUE 0b were landed with. Repos land in scratch as <repo>-bin, so no
# plan applies and nothing in the landed repositories is touched.
# Usage: sh tools/probes/ttf_sfd_origin/reland_vfb_from_binary.sh   (one land job at a time)
set -u
W=/home/fsanches/compartilhado/gf-source-modernization
P=$W/tools/probes/ttf_sfd_origin
export FAMILIES=$P/families-vfb-from-binary.tsv
export BF_TREE=/home/fsanches/compartilhado/babelfont-rs-worktrees/2026-11-02
export OUT=/home/fsanches/compartilhado/tmp/vfbimport-from-binary-2026-11-03/repos
export SCRATCH=/home/fsanches/compartilhado/tmp/vfbimport-from-binary-2026-11-03/scratch
export TMPDIR=/home/fsanches/compartilhado/tmp
LOGS=/home/fsanches/compartilhado/tmp/vfbimport-from-binary-2026-11-03/logs
mkdir -p "$OUT" "$SCRATCH" "$LOGS"
for repo in $(tail -n +2 "$FAMILIES" | cut -f1 | sort -u); do
    /home/fsanches/compartilhado/gftools/venv/bin/python3 -I "$W/tools/land.py" "$repo" --rebuild > "$LOGS/$repo.log" 2>&1
    grep -E "^$repo: " "$LOGS/$repo.log" | tail -1
done > "$LOGS/summary.txt"
echo done
