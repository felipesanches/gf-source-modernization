#!/bin/bash
# Question: built from the .sfd the release was actually exported from
# (googlefontdirectory-hg 2d042ebbd:ultra/src/Ultra-TTF.sfd, ModificationTime 1304463351
# == the release's FFTM sourceModified), with the pinned fidelity-only harness and NO
# .sfd edit, which rows does Ultra-Regular still have, and how many LTR pairs shape
# differently? (Compare: the pairing's 52f780bc .sfd is the 2011-10-17 re-save.)
# Output: runs/02-ultra-may-sfd/{Ultra-Regular.tsv,.gate.txt,pairs-ink.txt,fftm_source_commit.txt}
# Run: bash investigations/next-emptygpos-verify/probes/ultra_exported_sfd.sh
set -eu
W=/home/fsanches/compartilhado/gf-source-modernization
V=$W/investigations/next-emptygpos-verify
S=/home/fsanches/compartilhado/sfd-reland-scratch/emptygpos-verify
ARC=/home/fsanches/compartilhado/upstream_repos/repo_archive/googlefonts/googlefontdirectory-hg.git
PY=/home/fsanches/compartilhado/gftools/venv/bin/python3
mkdir -p $S/ultra-hist
git -C $ARC show 2d042ebbd:ultra/src/Ultra-TTF.sfd > $S/ultra-hist/Ultra-TTF-2d042ebbd.sfd
cd $W
FAMILIES=$W/families-next.tsv SRC_OVERRIDE=$S/ultra-hist/Ultra-TTF-2d042ebbd.sfd \
  BF=/home/fsanches/compartilhado/babelfont-rs-worktrees/integration-ff-prs/target-heights/release/babelfont \
  OUT=$V/runs/02-ultra-may-sfd TAG=emptygpos-verify-02 SCRATCH=$S bash tools/baseline.sh Ultra-Regular
$PY $V/probes/pairs_hb.py /home/fsanches/compartilhado/google/fonts/apache/ultra/Ultra-Regular.ttf \
  $S/baseline/Ultra-Regular-emptygpos-verify-02/fonts/ttf/Ultra-Regular.ttf --ink > $V/runs/02-ultra-may-sfd/pairs-ink.txt
$PY $W/investigations/next-provenance/probes/fftm_source_commit.py \
  /home/fsanches/compartilhado/google/fonts/apache/ultra/Ultra-Regular.ttf $ARC ultra/src/Ultra-TTF.sfd \
  > $V/runs/02-ultra-may-sfd/fftm_source_commit.txt
