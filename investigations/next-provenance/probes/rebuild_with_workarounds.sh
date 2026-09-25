#!/bin/bash
# Question answered: tools/baseline.sh measures a conversion WITHOUT the named tool
# workarounds that tools/land.py applies inside the convert commit
# (tools/workarounds.py: usWeightClass from the .sfd's TTFWeight while fontc 1.0.0
# ignores a static Glyphs source's weightClass; a fractional ItalicAngle). Which table
# rows remain once they are applied, exactly as land.py applies them?
#
# It takes a finished harness run (its scratch dir holds tree/ and sources/), copies it,
# runs workarounds.py on the converted .glyphs with the (possibly SRC_OVERRIDE'd) .sfd
# the harness converted, rebuilds with the same gftools-builder3, and gates it the way
# baseline.sh does.
#
# Usage: rebuild_with_workarounds.sh <harness scratch dir> <Style> <source path in tree> <shipped.ttf> <OUT dir>
# e.g.   rebuild_with_workarounds.sh /home/fsanches/compartilhado/sfd-reland-scratch/provenance/baseline/Thabit-provenance-t7 \
#            Thabit src/Thabit.sfd /home/fsanches/compartilhado/google/fonts/ofl/thabit/Thabit.ttf runs/t8-thabit-workarounds
set -euo pipefail
src_run=$1; style=$2; sfdpath=$3; shipped=$4; out=$5
W=/home/fsanches/compartilhado/sfd-reland
B3=/home/fsanches/compartilhado/builder3-worktrees/main-e851b8b/target/release/gftools-builder
D3=/home/fsanches/compartilhado/diffenator3-venv/bin/diffenator3
PY=/home/fsanches/compartilhado/gftools/venv/bin/python3
TG=/home/fsanches/compartilhado/sfd-batch5/tools/table_gate.py
d="$src_run-workarounds"
rm -rf "$d"; mkdir -p "$d" "$out"
cp -a "$src_run/tree" "$src_run/sources" "$d/"
log="$out/$style.gate.txt"; : > "$log"
echo "workarounds: $("$PY" "$W/tools/workarounds.py" "$d/sources/$style.glyphs" "$d/tree/$sfdpath" 2>&1 | tr '\n' ' ')" >> "$log"
(cd "$d" && timeout 900 "$B3" sources/config.yaml) >> "$log" 2>&1
built=$(ls "$d"/fonts/ttf/*.ttf)
"$D3" -J 1 --no-languages --no-match --json --succinct "$shipped" "$built" > "$d/d3.json" 2>/dev/null
"$PY" "$TG" "$d/d3.json" --fonts "$shipped" "$built" >> "$log" 2>&1 || true
n=$(sed -n 's/^\([0-9]\{1,\}\) blocking table difference(s).*/\1/p' "$log" | tail -1)
echo "$style: ${n:-GATE-DID-NOT-FINISH} blocking; d3 json $d/d3.json"
