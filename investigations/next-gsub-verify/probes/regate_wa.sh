#!/bin/bash
# Question answered (verifier's own copy, written independently of next-gsub/probes/regate.sh):
# for a style tools/baseline.sh already converted, which table rows remain once
#   WA=1  tools/workarounds.py (what tools/land.py applies inside the convert commit:
#         usWeightClass from the .sfd's TTFWeight, italic angle) is applied to the
#         SAME .glyphs the harness produced, from the SAME .sfd it converted, and/or
#   TG=   a different gate script is used (default: the shared sfd-batch5 table_gate.py)?
# The conversion is not repeated; the build uses the harness's own toolchain pins
# (gftools-builder3 e851b8b / fontc 1.0.0, diffenator3).
#
# Usage: RUN=<harness scratch dir> SRC=<.sfd it converted> OUT=<dir> [WA=1] [TG=<gate>] \
#        bash regate_wa.sh <Style>
set -uo pipefail
style=$1
W=/home/fsanches/compartilhado/gf-source-modernization
B3=/home/fsanches/compartilhado/builder3-worktrees/main-e851b8b/target/release/gftools-builder
D3=/home/fsanches/compartilhado/diffenator3-venv/bin/diffenator3
PY=/home/fsanches/compartilhado/gftools/venv/bin/python3
TG=${TG:-/home/fsanches/compartilhado/sfd-batch5/tools/table_gate.py}
WA=${WA:-1}
shipped=$(awk -F'\t' -v s="$style" 'NR>1 && $7==s {print $9}' "$W/families-next.tsv")
d="$RUN-verify-regate"; rm -rf "$d"; mkdir -p "$d" "$OUT"
cp -r "$RUN/sources" "$d/"
log="$OUT/$style.gate.txt"
{ echo "from $RUN; gate $TG md5 $(md5sum < "$TG" | cut -c1-8); WA=$WA"
  if [ "$WA" = 1 ]; then "$PY" "$W/tools/workarounds.py" "$d/sources/$style.glyphs" "$SRC"; fi; } > "$log" 2>&1
(cd "$d" && timeout 900 "$B3" sources/config.yaml) >> "$log.build" 2>&1 || { echo "$style BUILD-FAILED"; exit 1; }
built=$(ls "$d"/fonts/ttf/*.ttf)
"$D3" -J 1 --no-languages --no-match --json --succinct "$shipped" "$built" > "$d/d3.json" 2>/dev/null
"$PY" "$TG" "$d/d3.json" --fonts "$shipped" "$built" >> "$log" 2>&1
tail -1 "$log"
