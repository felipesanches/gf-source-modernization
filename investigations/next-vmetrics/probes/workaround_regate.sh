#!/bin/bash
# Question: once tools/land.py's workarounds (tools/workarounds.py: usWeightClass from
# the .sfd's TTFWeight as FEA, fontc 1.0.0 dropping a single master's instance
# weightClass; the fractional ItalicAngle) are applied to the .glyphs a harness run
# produced, which table rows still block?
#
# tools/baseline.sh measures the conversion WITHOUT those workarounds, so a style whose
# only remaining row is OS/2.us_weight_class reads BLOCKING there even though land.py
# closes it. This re-runs just the tail of the pipeline -- workarounds, gftools-builder3,
# diffenator3, table_gate -- on a COPY of the harness's scratch directory, with the same
# tool pins baseline.sh uses.
#
#   bash workaround_regate.sh <Style> <harness scratch dir> <out dir>
#   e.g. bash workaround_regate.sh MountainsofChristmas-Bold \
#        /home/fsanches/compartilhado/sfd-reland-scratch/vmetrics/baseline/MountainsofChristmas-Bold-vmetrics-02-legacy-offset-metrics \
#        ../runs/03-legacy-offset-metrics+workarounds
set -euo pipefail
style=$1; from=$2; out=$3
W=/home/fsanches/compartilhado/sfd-reland
B3=/home/fsanches/compartilhado/builder3-worktrees/main-e851b8b/target/release/gftools-builder
D3=/home/fsanches/compartilhado/diffenator3-venv/bin/diffenator3
PY=/home/fsanches/compartilhado/gftools/venv/bin/python3
TG=/home/fsanches/compartilhado/sfd-batch5/tools/table_gate.py
row=$(awk -F'\t' -v s="$style" 'NR>1 && $7==s' "${FAMILIES:-$W/families-next.tsv}")
IFS=$'\t' read -r repo fam lic kind base commit _ src shipped <<<"$row"
d="$from-workarounds"; rm -rf "$d"; cp -r "$from" "$d"; rm -rf "$d/fonts"
mkdir -p "$out"; log="$out/$style.gate.txt"; : > "$log"
echo "workarounds:" >> "$log"
"$PY" "$W/tools/workarounds.py" "$d/sources/$style.glyphs" "$d/tree/$src" | sed 's/^/  /' >> "$log"
(cd "$d" && timeout 900 "$B3" sources/config.yaml) > "$out/$style.build.log" 2>&1
built=$(ls "$d"/fonts/ttf/*.ttf)
"$D3" -J 1 --no-languages --no-match --json --succinct "$shipped" "$built" > "$d/d3.json" 2>/dev/null
"$PY" "$TG" "$d/d3.json" --fonts "$shipped" "$built" >> "$log" 2>&1
tail -1 "$log"
