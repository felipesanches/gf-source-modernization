#!/bin/sh
# Build each repository from its sources with the published builder and run minimal_transfer.py
# on every font it builds against the font google/fonts ships.
# Usage: sh run.sh <scratch dir> <repo>...     (a repo checked out in REPOS, else cloned from
# the repo archive's googlefonts/<repo>.git default branch)
set -eu
S=${1:?scratch dir}; shift
REPOS=${REPOS:-/home/fsanches/compartilhado/sfd-reland-repos}
ARC=/home/fsanches/compartilhado/upstream_repos/repo_archive/googlefonts
GF=${GF:-/home/fsanches/compartilhado/google/fonts}
B3=${B3:-/home/fsanches/compartilhado/tmp/gftools-rust-target/release/gftools-builder}
PY=${PY:-/home/fsanches/compartilhado/gftools/venv/bin/python3}
HERE=$(cd "$(dirname "$0")" && pwd)
for r in "$@"; do
  mkdir -p "${S:?}/${r:?}"
  if [ ! -d "$S/$r/fonts/ttf" ]; then
    if [ -d "$REPOS/$r/sources" ]; then cp -r "$REPOS/$r/sources" "$S/$r/"
    else git clone -q "$ARC/$r.git" "$S/$r/clone" && cp -r "$S/$r/clone/sources" "$S/$r/"; fi
    (cd "$S/$r" && "$B3" sources/config.yaml > build.log 2>&1) || true
  fi
  for f in "$S/$r"/fonts/ttf/*.ttf; do
    [ -f "$f" ] || { echo "== $r: no build"; continue; }
    name=$(basename "$f")
    shipped=$(find "$GF/ofl/$r" "$GF/apache/$r" "$GF/ufl/$r" -name "$name" 2>/dev/null | head -1)
    echo "== $r $name"
    [ -n "$shipped" ] || { echo "  no shipped font named $name"; continue; }
    "$PY" -I "$HERE/minimal_transfer.py" "$shipped" "$f" "$S/$r/$name.minimal.ttf" 2>&1 | grep -v "^Traceback" | tail -6
  done
done
