#!/bin/sh
# Build one landed gf-source-modernization repo, as committed, into builds/<repo>/ (scratch copy).
# usage: build_repo.sh <repo> [<sources-dir-override>]
set -e
O=/home/fsanches/compartilhado/tmp/reland-research/outlines
B3=/home/fsanches/compartilhado/tmp/gftools-rust-target/release/gftools-builder
r=$1; src=${2:-/home/fsanches/compartilhado/sfd-reland-repos/$r/sources}
d=$O/builds/${3:-$r}; rm -rf "$d"; mkdir -p "$d"; cp -r "$src" "$d/sources"
cd "$d" && nice -n 10 "$B3" sources/config.yaml > build.log 2>&1 || { echo "$r BUILD FAILED"; tail -5 build.log; exit 1; }
ls "$d/fonts/ttf"
