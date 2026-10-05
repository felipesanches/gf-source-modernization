#!/bin/bash
# Question: with these cumulative candidate edits applied to a COPY of the
# style's unmodified .sfd, which baseline-gate rows remain, and which closed or
# opened relative to the unmodified baseline (gf-source-modernization/baseline/<style>.gate.txt)?
# Usage: run_stage.sh <Style> <run-name> [--import "U+XXXX ..."] <edits.tsv> ...
#   edits are applied in order by apply_edits.py; --import runs
#   sfd-batch5/tools/drift/import_outlines.py for the listed codepoints (outlines
#   recovered from the RELEASED binary) AFTER the edit lists.
# EXTRA_FLAGS / DROP_FLAGS pass through to baseline.sh.
set -euo pipefail
I=/home/fsanches/compartilhado/gf-source-modernization/investigations/tuffy
R=/home/fsanches/compartilhado/gf-source-modernization
PY=/home/fsanches/compartilhado/gftools/venv/bin/python3
ARC=/home/fsanches/compartilhado/upstream_repos/repo_archive/googlefonts/googlefontdirectory-hg.git
C=52f780bc9d197280a9f430574e179a5f233c56b6
SCR=/tmp/claude-1000/-home-fsanches-compartilhado-GoogleFonts/f55394dc-b840-4055-b5b4-e2463e4b4dd8/scratchpad/inv-tuffy/stages
style=$1; name=$2; shift 2
imports=""
if [ "${1:-}" = "--import" ]; then imports=$2; shift 2; fi
out=$I/runs/$name; mkdir -p "$out" "$SCR"
src=$SCR/$style-$name.sfd
git -C "$ARC" show "$C:ofl/tuffy/src/$style-TTF.sfd" > "$src.0"
cp "$src.0" "$src"
: > "$out/edits.log"
for e in "$@"; do
  cp "$e" "$out/"; "$PY" "$I/probes/apply_edits.py" "$src" "$src.tmp" "$e" >> "$out/edits.log"; mv "$src.tmp" "$src"
done
if [ -n "$imports" ]; then
  "$PY" /home/fsanches/compartilhado/sfd-batch5/tools/drift/import_outlines.py "$src" \
    "/home/fsanches/compartilhado/google/fonts/ofl/tuffy/$style.ttf" "$src.tmp" $imports >> "$out/edits.log"
  mv "$src.tmp" "$src"
fi
diff "$src.0" "$src" > "$out/source.diff" || true
TAG=tuffy OUT=$out SRC_OVERRIDE=$src bash "$R/tools/baseline.sh" "$style" | tail -1
grep '^BLOCKING' "$R/baseline/$style.gate.txt" | sort > "$out/rows.before"
grep '^BLOCKING' "$out/$style.gate.txt" | sort > "$out/rows.after" || true
tail -1 "$out/$style.gate.txt"
echo "closed: $(comm -23 "$out/rows.before" "$out/rows.after" | wc -l)   opened: $(comm -13 "$out/rows.before" "$out/rows.after" | wc -l)"
comm -13 "$out/rows.before" "$out/rows.after" | sed 's/^/  OPENED /' | cut -c1-200
