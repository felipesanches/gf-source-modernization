#!/bin/bash
# Question answered: for every style of the "heights" unit, which blocking table rows
# does the harness (tools/baseline.sh, one build per style, paired by construction
# through families-next.tsv) report
#   before   converter integration-ff-prs 17ea899 (upstream 496e904 + babelfont
#            #91/#92/#93), unmodified sources -- the baseline-next measurement;
#   altuni   the same converter plus the proposed fix to #91 (a glyph is looked up by
#            its alternate codepoints too, as FontForge's SFFindGID does; scratch
#            build, see ../runs/BF-ALTUNI.txt), unmodified sources;
#   blues    converter 17ea899, sources with the proposed documented edit
#            (make_edits.sh: addprivate BlueValues from src/<X>.otf; Ledger also
#            nbspwidth);
#   final    the fixed converter AND the edits -- what the repositories would land.
# Builds run one at a time. Each run writes runs/<set>/<Style>.{tsv,gate.txt,src}
# (.src names the source converted).
#
# Run: bash runs.sh <set> [Style...]      set = before | altuni | blues | final
set -uo pipefail
H=$(cd "$(dirname "$0")/.." && pwd)
W=/home/fsanches/compartilhado/gf-source-modernization
EDITS=${EDITS:-/home/fsanches/compartilhado/sfd-reland-scratch/heights/edits}
BF0=/home/fsanches/compartilhado/babelfont-rs-worktrees/integration-ff-prs/target-heights/release/babelfont
BF1=${BF1:-/home/fsanches/compartilhado/sfd-reland-scratch/heights/bf-target/release/babelfont}
export FAMILIES=$W/families-next.tsv SCRATCH=/home/fsanches/compartilhado/sfd-reland-scratch/heights

ALL="KottaOne-Regular Ledger-Regular LilitaOne-Regular Lustria-Regular Macondo-Regular
Magra-Bold MergeOne-Regular OleoScript-Bold OleoScript-Regular OleoScriptSwashCaps-Bold
OleoScriptSwashCaps-Regular Rambla-Bold Rambla-BoldItalic Rosarivo-Italic Sail-Regular
TextMeOne-Regular"

set_=$1; shift
styles=${*:-$ALL}
case $set_ in
  before|blues) export BF=$BF0 ;;
  altuni|final) export BF=$BF1 ;;
  *) echo "unknown set $set_" >&2; exit 2 ;;
esac
export OUT=$H/runs/$set_ TAG=heights-$set_
mkdir -p "$OUT"
for s in $styles; do
  src=
  if [ "$set_" = blues ] || [ "$set_" = final ]; then
    if [ -e "$EDITS/$s-blues-nbsp.sfd" ]; then src=$EDITS/$s-blues-nbsp.sfd
    elif [ -e "$EDITS/$s-blues.sfd" ]; then src=$EDITS/$s-blues.sfd; fi
  fi
  if [ -n "$src" ]; then
    SRC_OVERRIDE=$src bash "$W/tools/baseline.sh" "$s"
    echo "SRC_OVERRIDE=$src" > "$OUT/$s.src"
  else
    echo "unmodified" > "$OUT/$s.src"
    bash "$W/tools/baseline.sh" "$s"
  fi
done
