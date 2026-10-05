#!/bin/bash
# Question answered: what exactly does each proposed documented .sfd edit of the
# "heights" unit do to the unmodified source? Writes one edited copy per style,
# made ONLY with tools/sfd_edit.py, so the harness can try it (SRC_OVERRIDE=).
#
#   <Style>-blues.sfd   addprivate BlueValues <value>: restores the PostScript
#                       BlueValues FontForge held when it exported the release (read
#                       from src/<X>.otf in the same base tree by otf_bluevalues.py,
#                       formatted as FontForge's CFF reader stored them)
#   Ledger-Regular-blues-nbsp.sfd   the same, then nbspwidth (U+00A0 takes the
#                       space's 281, as google/fonts 0436d99c0 "ledger: fixed nbsp
#                       width (#2353)" did to the binary)
#
# The unmodified source is read from the repo archive (googlefontdirectory-hg
# 52f780bc, the base tree of families-next.tsv); edited copies go to scratch.
#
# Run: bash make_edits.sh            (writes $EDITS/*.sfd and prints each edit's report)
set -euo pipefail
H=$(cd "$(dirname "$0")" && pwd)
W=/home/fsanches/compartilhado/gf-source-modernization
PY=/home/fsanches/compartilhado/gftools/venv/bin/python3
ARC=/home/fsanches/compartilhado/upstream_repos/repo_archive/googlefonts/googlefontdirectory-hg.git
EDITS=${EDITS:-/home/fsanches/compartilhado/sfd-reland-scratch/heights/edits}
mkdir -p "$EDITS"

BLUES="Ledger-Regular LilitaOne-Regular Lustria-Regular Magra-Bold MergeOne-Regular
OleoScript-Bold OleoScript-Regular OleoScriptSwashCaps-Bold OleoScriptSwashCaps-Regular
Rambla-Bold Rambla-BoldItalic Sail-Regular TextMeOne-Regular"

unmodified() {  # <Style> <out>
  local row; row=$(awk -F'\t' -v s="$1" 'NR>1 && $7==s' "$W/families-next.tsv")
  IFS=$'\t' read -r _repo fam lic _kind _base commit _style src _shipped <<<"$row"
  git -C "$ARC" show "$commit:$lic/$fam/$src" > "$2"
}

for s in $BLUES; do
  unmodified "$s" "$EDITS/$s.orig.sfd"
  args=$("$PY" "$H/otf_bluevalues.py" "$s" | cut -f3)
  cp "$EDITS/$s.orig.sfd" "$EDITS/$s-blues.sfd"
  echo -n "$s: "; "$PY" "$W/tools/sfd_edit.py" "$EDITS/$s-blues.sfd" addprivate $args
done
cp "$EDITS/Ledger-Regular-blues.sfd" "$EDITS/Ledger-Regular-blues-nbsp.sfd"
echo -n "Ledger-Regular (second edit): "
"$PY" "$W/tools/sfd_edit.py" "$EDITS/Ledger-Regular-blues-nbsp.sfd" nbspwidth
# each edited copy differs from its source only by the lines the edit adds
for s in $BLUES; do
  n=$(diff -a "$EDITS/$s.orig.sfd" "$EDITS/$s-blues.sfd" | grep -c '^[<>]' || true)
  echo "$s: $n line(s) differ from the unmodified source"
done
