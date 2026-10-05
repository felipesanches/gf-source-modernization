#!/bin/bash
# Question answered: Yellowtail's only ".sfd" is a Type 1 PFB that babelfont cannot read,
# so the SFD programme has no source to convert. How far is the designer's own FontLab
# source (hg 52f780b apache/yellowtail/src/Yellowtail-Regular.vfb), converted by babelfont
# with no flags and built with gftools-builder3, from the binary Google Fonts ships
# (google/fonts b5efa9c32e8f apache/yellowtail/Yellowtail-Regular.ttf)? The answer sizes
# what a VFB-path landing would have to reproduce as documented edits (Dave Crossland's
# 2011-07-18 FontForge simplification, the dropped kerning, FontForge's OS/2 and name
# defaults) -- it is a measurement, not a proposal to land from the VFB.
#
# Usage: yellowtail_vfb_measure.sh <OUT dir> [<babelfont>]
set -euo pipefail
out=$1; BF=${2:-/home/fsanches/compartilhado/babelfont-rs-worktrees/integration-ff-prs/target-heights/release/babelfont}
ARC=/home/fsanches/compartilhado/upstream_repos/repo_archive/googlefonts/googlefontdirectory-hg.git
B3=/home/fsanches/compartilhado/builder3-worktrees/main-e851b8b/target/release/gftools-builder
D3=/home/fsanches/compartilhado/diffenator3-venv/bin/diffenator3
PY=/home/fsanches/compartilhado/gftools/venv/bin/python3
TG=/home/fsanches/compartilhado/sfd-batch5/tools/table_gate.py
I=/home/fsanches/compartilhado/gf-source-modernization/investigations/next-provenance
shipped=/home/fsanches/compartilhado/google/fonts/apache/yellowtail/Yellowtail-Regular.ttf
d=/home/fsanches/compartilhado/sfd-reland-scratch/provenance/yellowtail-vfb
rm -rf "$d"; mkdir -p "$d/sources" "$out"
git -C "$ARC" show 52f780bc9d197280a9f430574e179a5f233c56b6:apache/yellowtail/src/Yellowtail-Regular.vfb > "$d/Yellowtail-Regular.vfb"
"$BF" "$d/Yellowtail-Regular.vfb" "$d/sources/Yellowtail-Regular.glyphs" > "$out/convert.log" 2>&1
{ echo "buildVariable: false"; echo "removeOutlineOverlaps: false"; echo "sources:"; echo "  - Yellowtail-Regular.glyphs"; } > "$d/sources/config.yaml"
(cd "$d" && timeout 900 "$B3" sources/config.yaml) > "$out/build.log" 2>&1
built=$(ls "$d"/fonts/ttf/*.ttf | head -1)
"$D3" -J 1 --no-languages --no-match --json --succinct "$shipped" "$built" > "$d/d3.json" 2>/dev/null
"$PY" "$TG" "$d/d3.json" --fonts "$shipped" "$built" > "$out/Yellowtail-Regular.gate.txt" 2>&1 || true
tail -1 "$out/Yellowtail-Regular.gate.txt"
grep -E '^ *BLOCKING' "$out/Yellowtail-Regular.gate.txt" | awk '{print $2}' | sed 's/\..*//' | sort | uniq -c
"$PY" "$I/probes/d3_render.py" "$d/d3.json" --list 5 | tee "$out/render.txt"
