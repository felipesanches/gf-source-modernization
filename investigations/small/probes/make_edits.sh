#!/bin/sh
# Question answered: what exactly are the edited .sfd copies the runs in ../runs/
# converted? Regenerates each one from the READ-ONLY repo archive with
# tools/sfd_edit.py, so every tested file is reproducible from the unmodified
# source plus one named operation.
#
# Usage: sh probes/make_edits.sh      (from investigations/small/)
# Output: edits/<name>.sfd  -- each prints what the field stated before the edit
set -eu
W=/home/fsanches/compartilhado/sfd-reland
ARC=/home/fsanches/compartilhado/upstream_repos/repo_archive
PY=/home/fsanches/compartilhado/gftools/venv/bin/python3
E="$W/investigations/small/edits"
mkdir -p "$E"

HG=$ARC/googlefonts/googlefontdirectory-hg.git
HGC=52f780bc9d197280a9f430574e179a5f233c56b6
CR=$ARC/loudifier/Comic-Relief.git
CRC=856315f5a45dfdad75090e4454f1ebfd019296b9

# (2) RussoOne: the documented edit proposed for the repository history
git -C "$HG" show "$HGC:ofl/russoone/src/RussoOne-Regular-TTF.sfd" > "$E/RussoOne-Regular-TTF.fstype0.sfd"
"$PY" "$W/tools/sfd_edit.py" "$E/RussoOne-Regular-TTF.fstype0.sfd" setfield FSType 0

# (1) ComicRelief: NOT a proposed edit. A SIMULATION of the proposed converter
# rule (post.underlinePosition = otRound(UnderlinePosition + UnderlineWidth/2)
# = otRound(-185 + 87.5) = -97): the value that rule would hand the compiler,
# written into a copy so the stock converter (run WITHOUT
# --fontforge-underline-position) carries it through unchanged.
for s in Regular Bold; do
  git -C "$CR" show "$CRC:sources/ComicRelief-$s.sfd" > "$E/ComicRelief-$s.upos-sim-97.sfd"
  "$PY" "$W/tools/sfd_edit.py" "$E/ComicRelief-$s.upos-sim-97.sfd" setfield UnderlinePosition -97
done
