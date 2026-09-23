#!/bin/sh
# Question answered: what did the FontForge that exported the Nosifer releases
# (FFTM FFTimeStamp 2011-02-22 = tag v20110222, commit 9ec8bff8) do with
# (1) the OS/2 heights and (2) GSUB/GPOS/kern, and when was (1) changed?
# Fetches the exact files from raw.githubusercontent.com (no GitHub API) and
# prints the load-bearing lines.  Usage: sh ff_evidence.sh <scratch-dir>
set -eu
D=${1:?scratch dir}; mkdir -p "$D"; cd "$D"
R=https://raw.githubusercontent.com/fontforge/fontforge
V=9ec8bff88ac76c3f753b85ac4c364a9cd72c61aa        # v20110222
FIX=4d34d21ef8662210f10b43f62e65767a818235cf      # 2012-05-14 Khaled Hosny's fix
for c in $V $FIX; do for f in splinefont.c tottf.c; do
  curl -sfL -o "$c-$f" "$R/$c/fontforge/$f"; done; done
echo "== v20110222 splinefont.c, SFStandardHeight no-flat-tops branch:"
grep -n -A6 'find the mean' "$V-splinefont.c"
echo "== $FIX (2012-05-14) splinefont.c, same branch:"
grep -n -A6 'find the mean' "$FIX-splinefont.c"
echo "== v20110222 tottf.c initATTables: layout tables only in opentypemode; legacy kern otherwise"
sed -n '/^static void initATTables/,/redoos2(at);/p' "$V-tottf.c"
echo "== v20110222 tottf.c: head created = time of generation"
grep -n -B1 'memcpy(head->createtime,head->modtime' "$V-tottf.c"
