#!/bin/bash
# Question: what changed between the Ultra .sfd the release was exported from
# (googlefontdirectory-hg 2d042ebbd, 2011-05-06) and the one the pairing uses
# (52f780bc == 10ef7b362 "Updating hinting of Ultra", 2011-10-17), and which hg binary
# is the one google/fonts shipped? Prints blob ids of each Ultra.ttf/.sfd revision,
# header-field and glyph-set differences, per-glyph kern (Kerns2) and KernClass2 counts,
# and whether any per-glyph kern list belongs to an A-group glyph.
# Run: bash investigations/next-emptygpos-verify/probes/ultra_sfd_history.sh > runs/02-ultra-may-sfd/sfd_history.txt
set -u
ARC=/home/fsanches/compartilhado/upstream_repos/repo_archive/googlefonts/googlefontdirectory-hg.git
T=52f780bc9d197280a9f430574e179a5f233c56b6
echo "== blob ids (same id == byte-identical)"
for x in 7f2fe1832:ultra/Ultra.ttf 2d042ebbd:ultra/Ultra.ttf 10ef7b362:ultra/Ultra.ttf $T:apache/ultra/Ultra.ttf \
         2d042ebbd:ultra/src/Ultra-TTF.sfd 10ef7b362:ultra/src/Ultra-TTF.sfd $T:apache/ultra/src/Ultra-TTF.sfd; do
  echo "$(git -C $ARC rev-parse $x) $x"; done
echo "google/fonts 90abd17b4:apache/ultra/Ultra.ttf $(git -C /home/fsanches/compartilhado/google/fonts rev-parse 90abd17b4:apache/ultra/Ultra.ttf)"
MAY=$(mktemp); OCT=$(mktemp)
git -C $ARC show 2d042ebbd:ultra/src/Ultra-TTF.sfd > $MAY; git -C $ARC show $T:apache/ultra/src/Ultra-TTF.sfd > $OCT
echo "== header fields (< May 2d042ebbd, > Oct 52f780bc)"
diff <(grep -a -E '^(Weight|TTFWeight|ModificationTime|CreationTime|Lookup: 258|KernClass2|BeginChars)' $MAY) \
     <(grep -a -E '^(Weight|TTFWeight|ModificationTime|CreationTime|Lookup: 258|KernClass2|BeginChars)' $OCT)
echo "== glyph set"
diff <(grep -a '^StartChar:' $MAY | sort) <(grep -a '^StartChar:' $OCT | sort)
echo "== kerning: Kerns2 lists May $(grep -a -c '^Kerns2:' $MAY), Oct $(grep -a -c '^Kerns2:' $OCT); KernClass2 May $(grep -a -c '^KernClass2:' $MAY), Oct $(grep -a -c '^KernClass2:' $OCT)"
echo "== A-group glyphs with a per-glyph kern list in May:"
awk '/^StartChar: /{g=$2} /^Kerns2:/{print g}' $MAY | grep -x -E 'A|Agrave|Aacute|Acircumflex|Atilde|Adieresis|Aring|Amacron|Abreve|Aogonek' || echo "  none"
rm -f $MAY $OCT
