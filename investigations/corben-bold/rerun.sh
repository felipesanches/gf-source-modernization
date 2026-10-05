#!/bin/bash
# Question answered: does each proposed Corben-Bold .sfd edit close its gate row(s)
# without opening others? Regenerates every candidate source from the repo archive
# (read-only: `git archive`, never a checkout) and runs tools/baseline.sh once per
# cumulative step, ONE BUILD AT A TIME. Results land in runs/<step>/.
#
# Usage: bash investigations/corben-bold/rerun.sh [scratch-dir]
set -euo pipefail
I=$(cd "$(dirname "$0")" && pwd)
W=$(cd "$I/../.." && pwd)                       # gf-source-modernization/
S=${1:-${TMPDIR:-/tmp}/inv-corben-bold}
ARC=/home/fsanches/compartilhado/upstream_repos/repo_archive/librefonts/corben.git
SC=/home/fsanches/compartilhado/sfd-batch5/tools/source_corrections.py
mkdir -p "$S/tree" "$S/cand"
git -C "$ARC" archive 94d5b00e6b64f85258d17e766a1e8e6d85554adc | tar -x -C "$S/tree"

python3 "$I/renameglyphgid.py" "$S/tree/src/Corben-Bold.sfd" "$S/cand/e1.sfd" 547 dcroat dcroat.1
cp "$S/cand/e1.sfd"   "$S/cand/e12.sfd";   python3 "$SC" "$I/e2-vmetrics.tsv" corben "$S/cand/e12.sfd"
cp "$S/cand/e12.sfd"  "$S/cand/e123.sfd";  python3 "$SC" "$I/e3-vendor.tsv"   corben "$S/cand/e123.sfd"
cp "$S/cand/e123.sfd" "$S/cand/e1234.sfd"; python3 "$SC" "$I/e4-panose.tsv"   corben "$S/cand/e1234.sfd"

run() {  # <out-name> <sfd> [DROP_FLAGS]
  DROP_FLAGS="${3:-}" TAG=corben-bold OUT="$I/runs/$1" SRC_OVERRIDE="$2" SCRATCH="$S" \
    bash "$W/tools/baseline.sh" Corben-Bold
  grep -E '^BLOCKING|blocking table' "$I/runs/$1/Corben-Bold.gate.txt" || true
}
run e1-dcroat1       "$S/cand/e1.sfd"      # expect: builds; 11 rows
run e12-vmetrics     "$S/cand/e12.sfd"     # expect: 5 rows
run e123-vendor      "$S/cand/e123.sfd"    # expect: 4 rows
run e1234-panose     "$S/cand/e1234.sfd"   # expect: 3 rows (weight, x-height, cap height)
run e1234-nodupcmap  "$S/cand/e1234.sfd" "--add-legacy-duplicate-cmap"   # expect: 3 rows, empty cmap_diff
