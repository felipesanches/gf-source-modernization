#!/bin/bash
# Question answered: for a style the harness (tools/baseline.sh) already converted,
# which table rows remain once
#   (a) tools/land.py's named toolchain workarounds are applied (WA=1:
#       tools/workarounds.py -- usWeightClass from the .sfd's TTFWeight, because
#       fontc 1.0.0 ignores a static Glyphs source's weightClass,
#       issues/fontc-static-weight-class.md), and/or
#   (b) the gate is a proposed revision instead of the shared one (TG=<gate script>)?
#
# It copies the harness run's .glyphs/config.yaml (the conversion is NOT repeated, so
# the converter and the source are exactly the run's), applies (a) to the SAME source
# the run converted, then repeats baseline.sh's build and gate steps with its tools:
# gftools-builder3 e851b8b (fontc 1.0.0), diffenator3, and the gate.
#
#   RUN=<harness scratch dir, e.g. $SCRATCH/baseline/Megrim-gsub-r1>
#   SRC=<the .sfd that run converted>      (needed for WA=1)
#   OUT=<dir for <Style>.gate.txt / .tsv>  WA=0|1 (default 1)
#   TG=<gate script> (default: the shared sfd-batch5/tools/table_gate.py)
#   bash regate.sh <Style>
set -uo pipefail
style=$1
W=/home/fsanches/compartilhado/sfd-reland
B3=/home/fsanches/compartilhado/builder3-worktrees/main-e851b8b/target/release/gftools-builder
D3=/home/fsanches/compartilhado/diffenator3-venv/bin/diffenator3
PY=/home/fsanches/compartilhado/gftools/venv/bin/python3
TG=${TG:-/home/fsanches/compartilhado/sfd-batch5/tools/table_gate.py}
WA=${WA:-1}
row=$(awk -F'\t' -v s="$style" 'NR>1 && $7==s' "$W/families-next.tsv")
IFS=$'\t' read -r repo fam lic kind base commit _ src shipped <<<"$row"
d="$RUN-regate"; rm -rf "$d"; mkdir -p "$d" "$OUT"
cp -r "$RUN/sources" "$d/"; rm -f "$d"/sources/*.ttf
log="$OUT/$style.gate.txt"
{ echo "from: $RUN"; echo "gate: $TG ($(md5sum < "$TG" | cut -c1-8))"
  if [ "$WA" = 1 ]; then echo -n "workarounds: "; "$PY" "$W/tools/workarounds.py" "$d/sources/$style.glyphs" "$SRC"; fi
} > "$log" 2>&1
if [ "$WA" = 1 ] || [ ! -d "$RUN/fonts" ]; then
  (cd "$d" && timeout 900 "$B3" sources/config.yaml) >> "$log" 2>&1 || { echo "$style BUILD-FAILED"; exit 1; }
else
  cp -r "$RUN/fonts" "$d/"
fi
built=$(ls "$d"/fonts/ttf/*.ttf)
"$D3" -J 1 --no-languages --no-match --json --succinct "$shipped" "$built" > "$d/d3.json" 2>/dev/null
gate=$("$PY" "$TG" "$d/d3.json" --fonts "$shipped" "$built" 2>&1)
printf '%s\n' "$gate" >> "$log"
n=$(printf '%s' "$gate" | sed -n 's/^\([0-9]\{1,\}\) blocking table difference(s).*/\1/p' | tail -1)
keys=$(printf '%s\n' "$gate" | awk '/^ *BLOCKING /{print $2}' | sort -u | paste -sd, -)
if [ -z "$n" ]; then v=GATE-DID-NOT-FINISH; elif [ "$n" = 0 ]; then v=CLEAN; else v=BLOCKING; fi
printf '%s\t%s\t%s\t%s\t%s\n' "$repo" "$style" "$v" "${n:--}" "${keys:--}" > "$OUT/$style.tsv"
echo "$style: $v ${n:--}"
