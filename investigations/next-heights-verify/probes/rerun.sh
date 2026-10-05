#!/bin/bash
# Question answered: how to regenerate every output under ../runs/ of the adversarial
# re-verification of unit "heights" (next batch), in order. Probes first (cheap, no
# builds), then the patched converter build, then the harness runs (one build per
# style, sequential).
#
# Run: bash rerun.sh probes | build | builds
set -uo pipefail
cd "$(dirname "$0")"
PY=/home/fsanches/compartilhado/gftools/venv/bin/python3
S=/home/fsanches/compartilhado/sfd-reland-scratch/heights-verify
case ${1:-} in
  probes)
    $PY facts.py > ../runs/facts.txt
    $PY otf_head_dates.py > ../runs/otf_head_dates.txt
    $PY blues_theory_all.py > ../runs/blues_theory_all.txt
    $PY rule_all_next.py > ../runs/rule_all_next.txt
    $PY altuni_arith.py > ../runs/altuni_arith.txt
    $PY ledger_history.py > ../runs/ledger_history.txt
    $PY make_edits.py > ../runs/make_edits.txt ;;
  build)
    # my own build of 17ea899 + the investigator's patch, from a git archive export
    mkdir -p $S/bf-src && cd $S/bf-src
    git -C /home/fsanches/compartilhado/babelfont-rs-worktrees/integration-ff-prs archive 17ea8995bb117b57e9f81c734239725c617375a8 | tar -x
    patch -p1 < /home/fsanches/compartilhado/gf-source-modernization/investigations/next-heights/probes/babelfont-altuni-lookup.patch
    sudo -n /usr/local/sbin/drop-caches
    CARGO_BUILD_JOBS=3 CARGO_TARGET_DIR=$S/bf-target cargo build --release -p babelfont --features cli ;;
  builds)
    bash runs.sh before
    bash runs.sh blues Ledger-Regular LilitaOne-Regular Lustria-Regular Magra-Bold MergeOne-Regular OleoScript-Bold OleoScript-Regular OleoScriptSwashCaps-Bold OleoScriptSwashCaps-Regular Rambla-Bold Rambla-BoldItalic Sail-Regular TextMeOne-Regular
    bash runs.sh altuni KottaOne-Regular Macondo-Regular Rosarivo-Italic
    bash runs.sh final
    bash gate_with_workarounds.sh final Magra-Bold OleoScript-Bold OleoScriptSwashCaps-Bold Rambla-Bold Rambla-BoldItalic
    bash runs.sh siblings-altuni Magra-Regular Rambla-Italic Rambla-Regular Rosarivo-Regular
    bash glyphs_diff.sh blues; bash glyphs_diff.sh altuni
    bash altuni_regression.sh > ../runs/altuni_regression.txt
    bash nothing_else_opened.sh > ../runs/nothing_else_opened.txt ;;
  *) echo "usage: rerun.sh probes|build|builds" >&2; exit 2 ;;
esac
