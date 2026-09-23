#!/bin/sh
# Rerun everything FINDINGS.md cites, in order, one build at a time.
# Usage: sh probes/rerun.sh      (from anywhere; ~2 minutes)
# Each baseline.sh run ends with its gate's "N blocking table difference(s)" line;
# a run whose gate.txt lacks that line did not finish.
set -eu
W=/home/fsanches/compartilhado/sfd-reland
I=$W/investigations/small
PY=/home/fsanches/compartilhado/gftools/venv/bin/python3
BFH=/home/fsanches/compartilhado/babelfont-rs-worktrees/gf-sfd-conversion/target-heights/release/babelfont  # ca43adc
cd "$I"
sh probes/make_edits.sh
"$PY" probes/release_facts.py            > runs/release_facts.txt
"$PY" probes/underline_rules.py          > runs/underline_rules.txt
sh probes/sfdlib_underline.sh            > runs/sfdlib_underline.txt 2>/dev/null
sh probes/convert_diffs.sh               > runs/convert_diffs.txt
sh probes/convert_diffs.sh "$BFH"        > runs/convert_diffs-ca43adc.txt
B="bash $W/tools/baseline.sh"
TAG=small OUT=$I/runs/russoone-fstype0             SRC_OVERRIDE=$I/edits/RussoOne-Regular-TTF.fstype0.sfd $B RussoOne-Regular
BF=$BFH TAG=small OUT=$I/runs/russoone-fstype0-ca43adc SRC_OVERRIDE=$I/edits/RussoOne-Regular-TTF.fstype0.sfd $B RussoOne-Regular
BF=$BFH TAG=small OUT=$I/runs/russoone-unmodified-ca43adc $B RussoOne-Regular
DROP_FLAGS=--fontforge-underline-position TAG=small OUT=$I/runs/comicrelief-regular-noflag $B ComicRelief-Regular
DROP_FLAGS=--fontforge-underline-position TAG=small OUT=$I/runs/comicrelief-regular-sim97 SRC_OVERRIDE=$I/edits/ComicRelief-Regular.upos-sim-97.sfd $B ComicRelief-Regular
DROP_FLAGS=--fontforge-underline-position TAG=small OUT=$I/runs/comicrelief-bold-noflag $B ComicRelief-Bold
DROP_FLAGS=--fontforge-underline-position TAG=small OUT=$I/runs/comicrelief-bold-sim97 SRC_OVERRIDE=$I/edits/ComicRelief-Bold.upos-sim-97.sfd $B ComicRelief-Bold
grep -H -E '^BLOCKING|blocking table difference' runs/*/*.gate.txt
