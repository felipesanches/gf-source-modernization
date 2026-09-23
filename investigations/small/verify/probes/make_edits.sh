#!/bin/sh
# Question answered: which exact .sfd copies did this verification convert?
# Rebuilds each from the READ-ONLY archive with tools/sfd_edit.py, independently of
# the investigation's own edits/ (they are compared, not reused).
#   RussoOne-Regular-TTF.FSType0.sfd       the proposed edit: setfield FSType 0
#   ComicRelief-<S>.SIM-upos-97.sfd        NOT an edit: simulates the proposed converter
#                                          rule's output (-97) for the stock converter
# Usage: sh verify/probes/make_edits.sh
set -eu
W=/home/fsanches/compartilhado/sfd-reland; E=$W/investigations/small/verify/edits
ARC=/home/fsanches/compartilhado/upstream_repos/repo_archive; PY=/home/fsanches/compartilhado/gftools/venv/bin/python3
mkdir -p "$E"
git -C $ARC/googlefonts/googlefontdirectory-hg.git show 52f780bc9d197280a9f430574e179a5f233c56b6:ofl/russoone/src/RussoOne-Regular-TTF.sfd > "$E/RussoOne-Regular-TTF.orig.sfd"
cp "$E/RussoOne-Regular-TTF.orig.sfd" "$E/RussoOne-Regular-TTF.FSType0.sfd"
$PY $W/tools/sfd_edit.py "$E/RussoOne-Regular-TTF.FSType0.sfd" setfield FSType 0
diff "$E/RussoOne-Regular-TTF.orig.sfd" "$E/RussoOne-Regular-TTF.FSType0.sfd" || true
for s in Regular Bold; do
  git -C $ARC/loudifier/Comic-Relief.git show 856315f5a45dfdad75090e4454f1ebfd019296b9:sources/ComicRelief-$s.sfd > "$E/ComicRelief-$s.orig.sfd"
  cp "$E/ComicRelief-$s.orig.sfd" "$E/ComicRelief-$s.SIM-upos-97.sfd"
  $PY $W/tools/sfd_edit.py "$E/ComicRelief-$s.SIM-upos-97.sfd" setfield UnderlinePosition -97
done
cmp "$E/RussoOne-Regular-TTF.FSType0.sfd" $W/investigations/small/edits/RussoOne-Regular-TTF.fstype0.sfd && echo "FSType0 copy identical to the investigation's"
