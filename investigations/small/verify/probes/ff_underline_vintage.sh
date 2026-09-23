#!/bin/sh
# Questions answered:
#  1. Which rule did each FontForge release's TTF exporter use for post.underlinePosition?
#     (tottf.c dumppost line; upos/uwidth are `real`, putshort takes int -> truncation)
#  2. Which FontForge first writes "SplineFontDB: 3.2" (the ComicRelief .sfd's header)?
# Fetches from raw.githubusercontent.com only (no GitHub API).
# Usage: sh verify/probes/ff_underline_vintage.sh
set -eu
S=/tmp/claude-1000/-home-fsanches-compartilhado-GoogleFonts/f55394dc-b840-4055-b5b4-e2463e4b4dd8/scratchpad/inv-small-verify/ff; mkdir -p $S
R=https://raw.githubusercontent.com/fontforge/fontforge
for t in 20170731 20190317 20200314 20230101; do
  curl -sfL -o $S/tottf-$t.c $R/$t/fontforge/tottf.c
  echo "$t tottf.c: $(grep 'putshort(at->post,sf->upos' $S/tottf-$t.c | sed 's/;.*//; s/^ *//')"
done
curl -sfL $R/20190317/fontforge/splinefont.h | grep -m1 'italicangle, upos, uwidth' | sed 's/^/20190317 splinefont.h: /'
for t in 20190317 20200314; do
  curl -sfL -o $S/sfd-$t.c $R/$t/fontforge/sfd.c
  echo "$t sfd.c SFDDump versions: $(grep -E '^ *double version = 3\.[0-9]' $S/sfd-$t.c | tr -s ' ' | tr '\n' ' ')"
done
A=/home/fsanches/compartilhado/upstream_repos/repo_archive/loudifier/Comic-Relief.git
for s in Regular Bold; do
  echo "ComicRelief-$s.sfd @856315f: $(git -C $A show 856315f5a45dfdad75090e4454f1ebfd019296b9:sources/ComicRelief-$s.sfd | grep -m4 -E '^(SplineFontDB|UnderlinePosition|UnderlineWidth|OS2XHeight):' | tr '\n' ' ')"
done
python3 -c "import math; p,w=-185,175; print('ComicRelief: FontForge>=20190317 trunc(p+w/2)=%d  sfdLib+ufo2ft floor(p+w/2+.5)=%d  FontForge<=2017 trunc(p-w/2)=%d  i32 naive p+w//2 (C/Rust trunc)=%d' % (int(p+w/2), math.floor(p+w/2+.5), int(p-w/2), p+int(w/2)))"
