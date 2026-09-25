#!/bin/sh
# Check a babelfont build's FontForge feature output on two real SFDs.
# Usage: PY=/path/to/python-with-fontTools ./run.sh BABELFONT_BIN OUTDIR
# BABELFONT_BIN: `cargo build -p babelfont --features cli --bin babelfont`.
set -eu
BIN=$(realpath "$1"); OUT=$2; HERE=$(cd "$(dirname "$0")" && pwd)
PY=${PY:-python3}
ARCH=/home/fsanches/compartilhado/upstream_repos/repo_archive/googlefonts/googlefontdirectory-hg.git
REV=52f780bc9d197280a9f430574e179a5f233c56b6
mkdir -p "$OUT"; cd "$OUT"
for spec in varela/src/Varela-Regular-TTF poly/src/Poly-Italic-TTF; do
    f=$(basename "$spec")
    git -C "$ARCH" show "$REV:ofl/$spec.sfd" > "$f.sfd"
    rm -rf "$f.ufo"
    "$BIN" "$f.sfd" "$f.ufo" > "$f.ufo.log" 2>&1
    "$BIN" "$f.sfd" "$f.ttf" > "$f.ttf.log" 2>&1
    "$PY" -c "import plistlib,sys; print('\n'.join(plistlib.load(open(sys.argv[1],'rb'))))" \
        "$f.ufo/glyphs/contents.plist" > "$f.glyphorder.txt"
    echo "== $f feaLib: $("$PY" "$HERE/check_sfd_vs_fealib.py" "$f.sfd" "$f.ufo/features.fea" "$f.glyphorder.txt" | tail -n 1)"
    echo "== $f fea-rs: $("$PY" "$HERE/check_sfd_vs_binary_counts.py" "$f.sfd" "$f.ufo/features.fea" "$f.ttf" | tail -n 1)"
done
