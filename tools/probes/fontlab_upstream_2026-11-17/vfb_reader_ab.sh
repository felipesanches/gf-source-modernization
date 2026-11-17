#!/bin/sh
# Question: which library .vfb files does each vfbreader build read (ok / error / panic)?
# Usage: vfb_reader_ab.sh <out.tsv> <label=vfbreader binary>...   (corpus: unique .vfb files under $C, default vfb-reland-repos-fixes)
out=$1; shift
C=${C:-/home/fsanches/compartilhado/vfb-reland-repos-fixes}
find "$C" -iname '*.vfb' -not -path '*/.git/*' | sort | while read -r f; do
  h=$(sha256sum "$f" | cut -c1-16)
  printf '%s\t%s' "$h" "${f#$C/}"
  for lb in "$@"; do
    b=${lb#*=}
    timeout 60 "$b" "$f" > /dev/null 2> ${TMPDIR:-/home/fsanches/compartilhado/tmp}/.vfbab.$$; rc=$?
    case $rc in 0) r=ok;; 1) r=error;; 101) r=panic;; 124) r=timeout;; *) r=rc$rc;; esac
    printf '\t%s' "$r"
  done
  printf '\n'
done | sort -u -k1,1 > "$out"
rm -f ${TMPDIR:-/home/fsanches/compartilhado/tmp}/.vfbab.$$
