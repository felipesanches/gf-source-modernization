#!/bin/bash
# Adversarial verification of unit "tuffy" -- reruns every measurement VERIFY.md quotes.
# Question: from the UNMODIFIED sources, with the edits re-implemented independently
# (verify_apply.py), do the investigation's proposed edits give the rows it reported,
# and what does the gate not see?
# Usage: bash rerun.sh            (one build at a time; ~15 builds, ~10 s each)
# Writes: $W/ (scratch; default below) -- sources, edited copies, runs/*.
set -euo pipefail
H=$(cd "$(dirname "$0")" && pwd)
W=${W:-/tmp/claude-1000/-home-fsanches-compartilhado-GoogleFonts/f55394dc-b840-4055-b5b4-e2463e4b4dd8/scratchpad/inv-tuffy-verify-rerun}
R=/home/fsanches/compartilhado/sfd-reland
PY=/home/fsanches/compartilhado/gftools/venv/bin/python3
D3=/home/fsanches/compartilhado/diffenator3-venv/bin/diffenator3
TG=/home/fsanches/compartilhado/sfd-batch5/tools/table_gate.py
IMP=/home/fsanches/compartilhado/sfd-batch5/tools/drift/import_outlines.py
ARC=/home/fsanches/compartilhado/upstream_repos/repo_archive/googlefonts/googlefontdirectory-hg.git
C=52f780bc9d197280a9f430574e179a5f233c56b6
GF=/home/fsanches/compartilhado/google/fonts/ofl
BFH=/home/fsanches/compartilhado/babelfont-rs-worktrees/gf-sfd-conversion/target-heights/release/babelfont
S=/tmp/claude-1000/-home-fsanches-compartilhado-GoogleFonts/f55394dc-b840-4055-b5b4-e2463e4b4dd8/scratchpad/baseline
mkdir -p "$W/src" "$W/edited" "$W/runs"
for s in Regular Italic Bold BoldItalic; do
  git -C "$ARC" show "$C:ofl/tuffy/src/Tuffy-$s-TTF.sfd" > "$W/src/Tuffy-$s-TTF.sfd"
  git -C "$ARC" show "$C:ofl/tuffy/Tuffy-$s.ttf" > "$W/src/mono-Tuffy-$s.ttf"   # FontForge 001.271 export
done
gate() {  # gate <Style> <run> [env...]: build with baseline.sh, keep the font
  local st=$1 run=$2; shift 2
  (cd "$R" && env "$@" TAG=tuffy-verify OUT="$W/runs/$run" bash tools/baseline.sh "$st")
  cp "$S/$st-tuffy-verify/fonts/ttf/"*.ttf "$W/runs/$run/built-$st.ttf"
  cp "$S/$st-tuffy-verify/d3.json" "$W/runs/$run/d3-$st.json"
}
A="$PY $H/verify_apply.py"
OS2R="setfield OS2SubXSize 1331 -- setfield OS2SubYSize 1228 -- setfield OS2SubXOff 0 -- setfield OS2SubYOff 153 -- setfield OS2SupXSize 1331 -- setfield OS2SupYSize 1228 -- setfield OS2SupXOff 0 -- setfield OS2SupYOff 716 -- setfield OS2StrikeYSize 50 -- setfield OS2StrikeYPos 300"
OS2I="setfield OS2SubXSize 1331 -- setfield OS2SubYSize 1228 -- setfield OS2SubXOff -32 -- setfield OS2SubYOff 153 -- setfield OS2SupXSize 1331 -- setfield OS2SupYSize 1228 -- setfield OS2SupXOff 150 -- setfield OS2SupYOff 716 -- setfield OS2StrikeYSize 50 -- setfield OS2StrikeYPos 300"
COMMON="setfield Version 1.272 -- setfield FSType 8 -- setencoding .null 0 0 -- setencoding nonmarkingreturn 13 13 -- ffnotdef -- translateglyph brevesubnosp -1302 0 -- setwidth brevesubnosp 0"
LATIN="setrefer Agrave 1 0 0 -- setrefer Aacute 1 0 0 -- setrefer Amacron 1 0 0 -- setrefer Iacute 1 0 0 -- setrefer eacute 1 0 0 -- setrefer uacute 1 0 0"
IOTA="setrefer alphaiotasub 1 0 0 -- setrefer alphaiotasub 2 801 0 -- setwidth alphaiotasub 2013 -- setrefer Alphaiotasub 2 801 0 -- setwidth Alphaiotasub 2103 -- setrefer etaiotasub 1 0 0 -- setrefer etaiotasub 2 801 0 -- setwidth etaiotasub 1865 -- setrefer Etaiotasub 1 0 0 -- setrefer Etaiotasub 2 801 0 -- setwidth Etaiotasub 1999 -- setrefer omegaiotasub 1 0 0 -- setrefer omegaiotasub 2 801 0 -- setwidth omegaiotasub 2009 -- setrefer Omegaiotasub 1 0 0 -- setrefer Omegaiotasub 2 801 0 -- setwidth Omegaiotasub 2159"
USERS="setrefer uni1E2A 1 1252 0 -- setrefer uni1E2B 1 1178 0"
PLUS4="setrefer uni221B 1 0 0 -- setrefer uni221C 1 0 0 -- setrefer etaiotasubgrave 1 0 0 -- setrefer etaiotasubacute 1 0 0"
$A "$W/src/Tuffy-Regular-TTF.sfd" "$W/edited/R.pre.sfd" $COMMON -- $OS2R -- $LATIN -- $IOTA -- $USERS
$PY "$IMP" "$W/edited/R.pre.sfd" "$GF/tuffy/Tuffy-Regular.ttf" "$W/edited/R-full.sfd" U+0162 U+0163
$A "$W/edited/R-full.sfd" "$W/edited/R-full-plus4.sfd" $PLUS4
$A "$W/edited/R-full-plus4.sfd" "$W/edited/R-full-plus4-heights.sfd" addfield OS2XHeight 500 -- addfield OS2CapHeight 700
$A "$W/src/Tuffy-Italic-TTF.sfd" "$W/edited/I.pre.sfd" $COMMON -- $OS2I
$PY "$IMP" "$W/edited/I.pre.sfd" "$GF/tuffy/Tuffy-Italic.ttf" "$W/edited/I-full.sfd" U+0162 U+0163 U+E257 U+03A9 U+1F6B U+004A U+00B7 U+0134 U+2076 U+2086 U+20B7
$A "$W/edited/I-full.sfd" "$W/edited/I-full-heights.sfd" addfield OS2XHeight 500 -- addfield OS2CapHeight 700

# 1. unmodified baselines (pinned babelfont f725e6a, gate as checked out)
for st in Tuffy-Regular Tuffy-Italic Tuffy-Bold Tuffy-BoldItalic; do gate $st base; done
# 2. all proposed edits; 3. plus the four composites the gate cannot see
gate Tuffy-Regular R-full SRC_OVERRIDE="$W/edited/R-full.sfd"
gate Tuffy-Italic I-full SRC_OVERRIDE="$W/edited/I-full.sfd"
gate Tuffy-Regular R-full-plus4 SRC_OVERRIDE="$W/edited/R-full-plus4.sfd"
# 4. the landing converter ca43adc (fills heights): without / with the height fields
gate Tuffy-Regular R-heights SRC_OVERRIDE="$W/edited/R-full-plus4.sfd" BF=$BFH
gate Tuffy-Regular R-heights-fields SRC_OVERRIDE="$W/edited/R-full-plus4-heights.sfd" BF=$BFH
gate Tuffy-Italic I-heights SRC_OVERRIDE="$W/edited/I-full.sfd" BF=$BFH
gate Tuffy-Italic I-heights-fields SRC_OVERRIDE="$W/edited/I-full-heights.sfd" BF=$BFH
for st in Tuffy-Bold Tuffy-BoldItalic; do gate $st bold-heights BF=$BFH; done
for f in "$W"/runs/*/*.gate.txt; do printf '%-60s %s\n' "${f#$W/runs/}" "$(tail -1 "$f")"; done

# 5. what the gate does not see: FreeType render comparison (unhinted, 1-bit, 1024 ppem)
REL_R=$GF/tuffy/Tuffy-Regular.ttf; REL_I=$GF/tuffy/Tuffy-Italic.ttf
$PY "$H/raster_scan.py" $REL_R "$W/runs/R-full/built-Tuffy-Regular.ttf" --min 0.01 > "$W/runs/raster-R-full.txt"
$PY "$H/raster_scan.py" $REL_R "$W/runs/R-full-plus4/built-Tuffy-Regular.ttf" --min 0.01 > "$W/runs/raster-R-full-plus4.txt"
$PY "$H/raster_scan.py" $REL_I "$W/runs/I-full/built-Tuffy-Italic.ttf" --min 0.01 > "$W/runs/raster-I-full.txt"
$PY "$H/raster_scan.py" "$W/src/mono-Tuffy-Regular.ttf" "$W/runs/R-full/built-Tuffy-Regular.ttf" --min 0 \
  --cps U+221B,U+221C,U+1FC2,U+1FC4,U+2208,U+10910 > "$W/runs/raster-R-ff1271-vs-ours.txt"
$PY "$H/raster_scan.py" $REL_R "$W/runs/base/built-Tuffy-Regular.ttf" --min 0 --cps U+0162,U+0163 > "$W/runs/raster-R-base-tcomma.txt"
$PY "$H/raster_scan.py" $REL_I "$W/runs/base/built-Tuffy-Italic.ttf" --min 0 \
  --cps U+0162,U+0163,U+E257,U+03A9,U+1F6B,U+004A,U+00B7,U+0134,U+2076,U+2086,U+20B7 > "$W/runs/raster-I-base-imports.txt"
$PY "$H/raster_scan.py" $REL_I "$W/runs/base/built-Tuffy-Italic.ttf" --min 0.005 > "$W/runs/raster-I-base.txt"
$PY "$H/component_moves.py" "$W/src/mono-Tuffy-Regular.ttf" $REL_R > "$W/runs/component-moves-R-ff1271-vs-v1272.txt"
$PY "$H/component_moves.py" "$W/runs/R-full/built-Tuffy-Regular.ttf" $REL_R > "$W/runs/component-moves-R-full-vs-v1272.txt"
$PY "$H/component_moves.py" "$W/runs/R-full-plus4/built-Tuffy-Regular.ttf" $REL_R > "$W/runs/component-moves-R-plus4-vs-v1272.txt"
# 6. gate variants: contour split at closePath (now upstream as sfd-batch5 cd4f827), and
#    "either per-contour or filled-region area" (overlap-invariant), on the unmodified builds
$PY "$H/gate_contour_split.py" "$W/runs/R-full/d3-Tuffy-Regular.json" --fonts $REL_R "$W/runs/R-full/built-Tuffy-Regular.ttf" > "$W/runs/gate-split-R-full.txt" 2>&1 || true
$PY "$H/gate_contour_split.py" "$W/runs/I-full/d3-Tuffy-Italic.json" --fonts $REL_I "$W/runs/I-full/built-Tuffy-Italic.ttf" > "$W/runs/gate-split-I-full.txt" 2>&1 || true
for st in Tuffy-Regular Tuffy-Italic; do
  $PY "$H/gate_either_area.py" "$W/runs/base/d3-$st.json" --fonts "$GF/tuffy/$st.ttf" "$W/runs/base/built-$st.ttf" > "$W/runs/gate-either-base-$st.txt" 2>&1 || true
done
$PY "$H/gate_either_area.py" --control "$GF/allerta/Allerta-Regular.ttf" "$GF/allertastencil/AllertaStencil-Regular.ttf" > "$W/runs/gate-either-control.txt"
# 7. our unmodified build against the FontForge 001.271 export (the 2015-2017 google/fonts binary)
for st in Tuffy-Regular Tuffy-Italic; do
  "$D3" -J 1 --no-languages --no-match --json --succinct "$W/src/mono-$st.ttf" "$W/runs/base/built-$st.ttf" > "$W/runs/d3-vs-ff1271-$st.json" 2>/dev/null
  $PY "$TG" "$W/runs/d3-vs-ff1271-$st.json" --fonts "$W/src/mono-$st.ttf" "$W/runs/base/built-$st.ttf" > "$W/runs/gate-vs-ff1271-$st.txt" 2>&1 || true
done
for f in "$W"/runs/*.txt; do printf '%-50s %s\n' "${f#$W/runs/}" "$(tail -1 "$f")"; done
