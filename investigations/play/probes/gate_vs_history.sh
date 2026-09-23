#!/bin/bash
# Question answered: which Play release does the .sfd conversion actually match?
# Gates ONE built font (our conversion of ofl/play/src/Play-<Style>-TTF.sfd at hg
# 52f780bc9d) against every Play-<Style>.ttf google/fonts has ever shipped, with the
# same diffenator3 + table_gate.py the baseline uses. Fewer blocking rows = closer.
#
# Usage: probes/gate_vs_history.sh <Style> <built.ttf> [outdir]
#   e.g. probes/gate_vs_history.sh Regular \
#     $SCRATCH/baseline/Play-Regular-play/fonts/ttf/Play-Regular.ttf runs/history
# Output: <outdir>/<Style>-<gfcommit>.gate.txt, and one summary line per release.
set -uo pipefail
style=$1; built=$2; out=${3:-$(dirname "$0")/../runs/history}
GF=/home/fsanches/compartilhado/google/fonts
D3=/home/fsanches/compartilhado/diffenator3-venv/bin/diffenator3
PY=/home/fsanches/compartilhado/gftools/venv/bin/python3
TG=/home/fsanches/compartilhado/sfd-batch5/tools/table_gate.py
mkdir -p "$out"; tmp=$(mktemp -d)
# google/fonts commits that changed ofl/play binaries (oldest first)
for c in 90abd17b4 81f1b67e7 cb02103dc ba2e464c4 e36afc756; do
  rel="$tmp/Play-$style-$c.ttf"
  git -C "$GF" show "$c:ofl/play/Play-$style.ttf" > "$rel"
  ver=$("$PY" -c "from fontTools.ttLib import TTFont;f=TTFont('$rel');print(f['name'].getDebugName(5), len(f.getGlyphOrder()), 'glyphs')")
  "$D3" -J 1 --no-languages --no-match --json --succinct "$rel" "$built" > "$tmp/d3.json" 2>/dev/null
  "$PY" "$TG" "$tmp/d3.json" --fonts "$rel" "$built" > "$out/$style-$c.gate.txt" 2>&1
  printf '%s\t%s\t%s\n' "$c" "$ver" "$(tail -1 "$out/$style-$c.gate.txt")"
done
rm -rf "$tmp"
