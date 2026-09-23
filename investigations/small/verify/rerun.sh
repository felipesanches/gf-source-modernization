#!/bin/sh
# Rerun everything VERIFY.md cites, in order, ONE build at a time (~3 minutes).
# Writes only under investigations/small/verify/ and the session scratchpad.
# Each harness run must end with its gate's "N blocking table difference(s)" line.
# Usage: sh /home/fsanches/compartilhado/sfd-reland/investigations/small/verify/rerun.sh
set -eu
W=/home/fsanches/compartilhado/sfd-reland; V=$W/investigations/small/verify
PY=/home/fsanches/compartilhado/gftools/venv/bin/python3
BFH=/home/fsanches/compartilhado/babelfont-rs-worktrees/gf-sfd-conversion/target-heights/release/babelfont  # ca43adc
export SCRATCH=/tmp/claude-1000/-home-fsanches-compartilhado-GoogleFonts/f55394dc-b840-4055-b5b4-e2463e4b4dd8/scratchpad/inv-small-verify
export TAG=small-verify
sh $V/probes/make_edits.sh                      > $V/runs/make_edits.txt
sh $V/probes/conv_checks.sh                     > $V/runs/conv_checks.txt
sh $V/probes/ff_underline_vintage.sh            > $V/runs/ff_underline_vintage.txt
$PY $V/probes/binary_facts.py                   > $V/runs/binary_facts.txt
$PY $W/tools/ff_heights_oracle.py $W/families.tsv 2>&1 | grep -E 'RussoOne|ComicRelief|^style|reproduces' > $V/runs/heights_oracle.txt || true
sh $W/investigations/small/probes/sfdlib_underline.sh $SCRATCH/sfdlib 2>/dev/null > $V/runs/sfdlib_underline.txt
B="bash $W/tools/baseline.sh"
OUT=$V/runs/russoone-FSType0-f725e6a SRC_OVERRIDE=$V/edits/RussoOne-Regular-TTF.FSType0.sfd $B RussoOne-Regular
BF=$BFH OUT=$V/runs/russoone-FSType0-ca43adc SRC_OVERRIDE=$V/edits/RussoOne-Regular-TTF.FSType0.sfd $B RussoOne-Regular
for s in Regular Bold; do l=$(echo $s | tr A-Z a-z)
  DROP_FLAGS=--fontforge-underline-position OUT=$V/runs/comicrelief-$l-noflag-f725e6a $B ComicRelief-$s
  DROP_FLAGS=--fontforge-underline-position OUT=$V/runs/comicrelief-$l-sim97-f725e6a SRC_OVERRIDE=$V/edits/ComicRelief-$s.SIM-upos-97.sfd $B ComicRelief-$s
  BF=$BFH DROP_FLAGS=--fontforge-underline-position OUT=$V/runs/comicrelief-$l-sim97-ca43adc SRC_OVERRIDE=$V/edits/ComicRelief-$s.SIM-upos-97.sfd $B ComicRelief-$s
done
grep -H -E '^BLOCKING|blocking table difference' $V/runs/*/*.gate.txt | sed "s|$V/||" > $V/runs/gate_summary.txt
cat $V/runs/gate_summary.txt
