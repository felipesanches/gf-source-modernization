#!/bin/bash
# Question answered: Lohit-Bengali passes the table gate (CLEAN) yet diffenator3 renders
# 284 Bengali words differently: no below/above-base mark is positioned. The release's
# abvm = [mark-to-base (Anchor-0/1), chain-context (lookup 2)] and blwm = [mark-to-base
# (Anchor-2)]. babelfont leaves the anchor lookups to the compiler (fontc rebuilds mark
# features from anchors) but writes the chain-context lookup as `feature abvm`, and fontc
# does not generate a feature the source already declares -- so abvm/blwm lose their
# mark-to-base rules. Does an insertion marker ("# Automatic Code", which fontc and ufo2ft
# honour) in the declared abvm feature restore them?
#
# It copies a finished harness run, inserts the marker at the top of the named feature's
# code in the converted .glyphs, rebuilds with gftools-builder3, gates it and counts the
# rendering diffs.
#
# Usage: mark_feature_marker.sh <harness scratch dir> <Style> <feature tag> <shipped.ttf> <OUT dir>
set -euo pipefail
src_run=$1; style=$2; tag=$3; shipped=$4; out=$5
B3=/home/fsanches/compartilhado/builder3-worktrees/main-e851b8b/target/release/gftools-builder
D3=/home/fsanches/compartilhado/diffenator3-venv/bin/diffenator3
PY=/home/fsanches/compartilhado/gftools/venv/bin/python3
TG=/home/fsanches/compartilhado/sfd-batch5/tools/table_gate.py
I=/home/fsanches/compartilhado/gf-source-modernization/investigations/next-provenance
d="$src_run-marker"
rm -rf "$d"; mkdir -p "$d" "$out"
cp -a "$src_run/sources" "$d/"
"$PY" - "$d/sources/$style.glyphs" "$tag" <<'EOF'
import re, sys
p, tag = sys.argv[1], sys.argv[2]
t = open(p, encoding="utf-8").read()
m = re.search(r'\{\ncode = "((?:[^"\\]|\\.)*)";\ntag = %s;\n\}' % re.escape(tag), t)
if not m:
    sys.exit("no feature %s" % tag)
t = t[:m.start(1)] + "# Automatic Code\n" + t[m.start(1):]
open(p, "w", encoding="utf-8").write(t)
print("marker inserted in feature", tag)
EOF
log="$out/$style.gate.txt"
(cd "$d" && timeout 900 "$B3" sources/config.yaml) > "$log" 2>&1
built=$(ls "$d"/fonts/ttf/*.ttf)
"$D3" -J 1 --no-languages --no-match --json --succinct "$shipped" "$built" > "$d/d3.json" 2>/dev/null
"$PY" "$TG" "$d/d3.json" --fonts "$shipped" "$built" >> "$log" 2>&1 || true
grep -E '^[0-9]+ blocking' "$log" | tail -1
"$PY" "$I/probes/d3_render.py" "$d/d3.json" --list 5
