#!/bin/bash
# (Copied from ../../next-heights/probes/gate_with_workarounds.sh for the adversarial
# re-run; only the scratch root, the run-directory tag and the .src parsing differ.)
# Question answered: once tools/land.py's named toolchain workarounds are applied
# (tools/workarounds.py: usWeightClass from the .sfd's TTFWeight, because fontc 1.0.0
# ignores a static Glyphs source's weightClass -- issues/fontc-static-weight-class.md),
# does a style that runs.sh measured still have any blocking row?
#
# It reuses the harness's own conversion of that run (the .glyphs baseline.sh wrote
# under $SCRATCH/baseline/<Style>-heights-<set>/), applies workarounds.py with the
# SAME source the run converted, then repeats baseline.sh's build and gate steps with
# its exact tools (gftools-builder3 e851b8b, diffenator3, sfd-batch5 table_gate.py).
# Output: runs/<set>-workarounds/<Style>.gate.txt (+ .tsv).
#
# Run: bash gate_with_workarounds.sh <set> <Style>...
set -uo pipefail
H=$(cd "$(dirname "$0")/.." && pwd)
W=/home/fsanches/compartilhado/sfd-reland
SCRATCH=/home/fsanches/compartilhado/sfd-reland-scratch/heights-verify
B3=/home/fsanches/compartilhado/builder3-worktrees/main-e851b8b/target/release/gftools-builder
D3=/home/fsanches/compartilhado/diffenator3-venv/bin/diffenator3
PY=/home/fsanches/compartilhado/gftools/venv/bin/python3
TG=/home/fsanches/compartilhado/sfd-batch5/tools/table_gate.py
ARC=/home/fsanches/compartilhado/upstream_repos/repo_archive
set_=$1; shift
OUT=$H/runs/$set_-workarounds; mkdir -p "$OUT"
for s in "$@"; do
  src_d=$SCRATCH/baseline/$s-heights-verify-$set_
  d=$SCRATCH/baseline/$s-heights-verify-$set_-wa
  rm -rf "$d"; mkdir -p "$d"; cp -r "$src_d/sources" "$d/"
  rm -f "$d"/sources/*.ttf
  row=$(awk -F'\t' -v s="$s" 'NR>1 && $7==s' "$W/families-next.tsv")
  IFS=$'\t' read -r repo fam lic kind base commit _ src shipped <<<"$row"
  over=$(cut -d" " -f1 "$H/runs/$set_/$s.src")
  if [ "$over" = unmodified ]; then
    git -C "$ARC/$base.git" show "$commit:$lic/$fam/$src" > "$d/source.sfd"
  else
    cp "${over#SRC_OVERRIDE=}" "$d/source.sfd"
  fi
  log=$OUT/$s.gate.txt
  { echo "from: $src_d ($over)"; echo -n "workarounds: "
    "$PY" "$W/tools/workarounds.py" "$d/sources/$s.glyphs" "$d/source.sfd"; } > "$log" 2>&1
  (cd "$d" && timeout 900 "$B3" sources/config.yaml) >> "$log" 2>&1 || { echo "$s BUILD-FAILED"; continue; }
  built=$(ls "$d"/fonts/ttf/*.ttf)
  "$D3" -J 1 --no-languages --no-match --json --succinct "$shipped" "$built" > "$d/d3.json" 2>/dev/null
  gate=$("$PY" "$TG" "$d/d3.json" --fonts "$shipped" "$built" 2>&1)
  printf '%s\n' "$gate" >> "$log"
  n=$(printf '%s' "$gate" | sed -n 's/^\([0-9]\{1,\}\) blocking table difference(s).*/\1/p' | tail -1)
  keys=$(printf '%s\n' "$gate" | awk '/^ *BLOCKING /{print $2}' | sort -u | paste -sd, -)
  if [ -z "$n" ]; then v=GATE-DID-NOT-FINISH; elif [ "$n" = 0 ]; then v=CLEAN; else v=BLOCKING; fi
  printf '%s\t%s\t%s\t%s\t%s\n' "$repo" "$s" "$v" "${n:--}" "${keys:--}" > "$OUT/$s.tsv"
  echo "$s: $v ${n:--}"
done
