#!/bin/sh
# Question answered: of the families RESIDUAL from their binaries (reland_vfb_from_binary.sh), which land
# CLEAN once the source states the release's GDEF glyph classes (land.py plan key gdef_classes_fea,
# as Carlito's does: the classes no category expresses, Simon on babelfont#131 -- "a matter for its
# source")? Probe plans are written to scratch and read through PLANS=; nothing is committed.
set -u
W=/home/fsanches/compartilhado/gf-source-modernization
P=$W/tools/probes/ttf_sfd_origin
S=/home/fsanches/compartilhado/tmp/vfbimport-from-binary-2026-11-03
export FAMILIES=$P/families-vfb-from-binary.tsv
export BF_TREE=/home/fsanches/compartilhado/babelfont-rs-worktrees/2026-11-02
export OUT=$S/repos-gdef SCRATCH=$S/scratch PLANS=$S/plans-gdef TMPDIR=/home/fsanches/compartilhado/tmp
mkdir -p "$OUT" "$S/logs-gdef"
for repo in $(cat "$S/residual.txt"); do
    /home/fsanches/compartilhado/gftools/venv/bin/python3 -I "$W/tools/land.py" "$repo" --rebuild > "$S/logs-gdef/$repo.log" 2>&1
    grep -E "^$repo: " "$S/logs-gdef/$repo.log" | tail -1
done > "$S/logs-gdef/summary.txt"
echo done
