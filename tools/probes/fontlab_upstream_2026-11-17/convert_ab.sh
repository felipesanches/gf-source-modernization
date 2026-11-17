#!/bin/sh
# Question: do two babelfont builds write the same .glyphs for every library .vfb?
# Usage: [C=<corpus dir>] convert_ab.sh <outdir> <label=babelfont binary>...   -> <outdir>/convert-ab.tsv
# Columns: sha256 prefix, path, per label: ok/fail, then "same" or "DIFF" (every ok output against the first label's).
out=$1; shift
C=${C:-/home/fsanches/compartilhado/vfb-reland-repos-fixes}
mkdir -p "$out"
find "$C" -iname '*.vfb' -not -path '*/.git/*' | sort | while read -r f; do
  h=$(sha256sum "$f" | cut -c1-16)
  [ -e "$out/$h.seen" ] && continue; : > "$out/$h.seen"
  line="$h	${f#$C/}"; first=; verdict=same
  for lb in "$@"; do
    l=${lb%%=*}; b=${lb#*=}
    if timeout 120 "$b" "$f" "$out/$h.$l.glyphs" > "$out/$h.$l.log" 2>&1 && [ -s "$out/$h.$l.glyphs" ]; then r=ok; else r=fail; fi
    line="$line	$r"
    if [ -z "$first" ]; then first=$l; elif ! cmp -s "$out/$h.$first.glyphs" "$out/$h.$l.glyphs"; then verdict=DIFF; fi
  done
  printf '%s\t%s\n' "$line" "$verdict"
done > "$out/convert-ab.tsv"
