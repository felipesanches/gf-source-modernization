#!/bin/sh
# Question answered: will fontc_crater's two kinds of target build for these landed
# repositories? Per repo, at its HEAD:
#   default mode -- every sources/*.glyphs through fontmake with the flags ttx_diff
#     passes by default (-o ttf --drop-implied-oncurves --keep-overlaps; production
#     names on). fontc already compiled the same sources in the landing gate.
#   gftools mode -- Python gftools builder on sources/config.yaml, as ttx_diff runs it
#     (--experimental-simple-output, --experimental-single-source), one repo only, since
#     the config is the same shape for all of them.
# Signal: fontmake exit status per source ("0 <path>" = built); the builder's last error.
#   sh crater_builds.sh <scratch dir> <repo>...
set -eu
PYBIN=/home/fsanches/compartilhado/gftools/venv/bin
REPOS=/home/fsanches/compartilhado/sfd-reland-repos
S=${1:?scratch dir}; shift
mkdir -p "$S"; cd "$S"
for r in "$@"; do
  mkdir -p "$r" && git -C "$REPOS/$r" archive HEAD sources | tar -x -C "$r"
done
ls ./*/sources/*.glyphs | xargs -P 4 -I{} sh -c 'd=$(dirname {}); n=$(basename {} .glyphs);
  cd $d && timeout 600 '"$PYBIN"'/fontmake -o ttf --output-path $n.fm.ttf \
    --drop-implied-oncurves --keep-overlaps $n.glyphs > $n.fm.log 2>&1; echo "$? {}"' \
  | sort -k2 > fontmake.txt
echo "default mode, fontmake: $(grep -c '^0 ' fontmake.txt) of $(wc -l < fontmake.txt) sources build"
grep -v '^0 ' fontmake.txt || true
r=$1; g=$(ls "$r"/sources/*.glyphs | head -1)
( cd "$r/sources" && timeout 300 "$PYBIN"/gftools builder config.yaml \
    --experimental-simple-output "$S/gftools-out" \
    --experimental-single-source "$(basename "$g")" > "$S/gftools.log" 2>&1 ) && \
  echo "gftools mode ($r): builds" || \
  echo "gftools mode ($r): FAILS -- $(grep -o "unexpected key not in schema '[A-Za-z]*'\|ValueError: .*" "$S/gftools.log" | head -2 | tr '\n' ' ')"
