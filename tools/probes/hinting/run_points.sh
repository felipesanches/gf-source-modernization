#!/bin/sh
# Build each named landed repository with the published builder and compare its glyph
# points with the font google/fonts ships (points.py), one block per font.
# Usage: run_points.sh <scratch dir> <repo>... > points.txt
# Env: REPOS (landed clones, default /home/fsanches/compartilhado/sfd-reland-repos),
#      GF (google/fonts clone), B3 (gftools-builder), PY (Python with fontTools).
set -eu
S=${1:?scratch dir}; shift
REPOS=${REPOS:-/home/fsanches/compartilhado/sfd-reland-repos}
GF=${GF:-/home/fsanches/compartilhado/google/fonts}
B3=${B3:-/home/fsanches/compartilhado/tmp/gftools-rust-target/release/gftools-builder}
PY=${PY:-/home/fsanches/compartilhado/gftools/venv/bin/python3}
HERE=$(cd "$(dirname "$0")" && pwd)
for r in "$@"; do
  mkdir -p "${S:?}/${r:?}"
  if [ ! -d "$S/$r/fonts/ttf" ]; then
    cp -r "$REPOS/$r/sources" "$S/$r/"
    (cd "$S/$r" && "$B3" sources/config.yaml > build.log 2>&1)
  fi
  for f in "$S/$r"/fonts/ttf/*.ttf; do
    name=$(basename "$f")
    shipped=$(find "$GF/ofl/$r" "$GF/apache/$r" "$GF/ufl/$r" -name "$name" 2>/dev/null | head -1)
    echo "== $r $name"
    "$PY" -I "$HERE/points.py" "$shipped" "$f"
  done
done
