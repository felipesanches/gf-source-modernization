#!/bin/bash
# Rerun every measurement of the "heights" unit of the next batch, in order.
# Each script's docstring/header states the question it answers; in short:
#
#   facts.py               release OS/2 + FFTM, -TTF.sfd header, src/<X>.otf OS/2+CFF
#                          BlueValues, side by side                  -> runs/facts.txt
#   hypotheses.py          which (FontForge vintage x outlines x BlueValues) reproduces
#                          each released sxHeight/sCapHeight          -> runs/hypotheses.txt
#   hypotheses.py dump S   per-glyph tops (why KottaOne/Macondo/Rosarivo-Italic differ:
#                          mu U+00B5 with AltUni2 U+03BC)             -> runs/dump-S.txt
#   provenance.py          is the -TTF.sfd a re-import of the release TTF (times, prep,
#                          gasp, every glyph's advance + point bbox)  -> runs/provenance.txt
#   ledger_release_history.py  what google/fonts 0436d99c0 / f8265bddf changed
#                                                                     -> runs/ledger_release_history.txt
#   otf_bluevalues.py      the BlueValues FontForge read from src/<X>.otf -> runs/otf_bluevalues.tsv
#   make_edits.sh          the edited sources (tools/sfd_edit.py addprivate / nbspwidth)
#   runs.sh <set>          harness runs: before | altuni | blues | final -> runs/<set>/
#   gate_with_workarounds.sh <set> <Style>...  + land.py's weight-class workaround
#                                                                     -> runs/<set>-workarounds/
#   nothing_else_opened.sh <a> <b>  no gate line changed except the closed rows
#   altuni_regression.py   the #91 fix across all 149 styles of both batches (conversion only)
#                                                                     -> runs/altuni_regression.txt
#   babelfont-altuni-lookup.patch   the proposed #91 follow-up (applied to a scratch
#                          worktree of integration-ff-prs 17ea899; runs/BF-ALTUNI.txt)
#   ff_heights_oracle-altuni.patch  the same lookup for tools/ff_heights_oracle.py
#
# The patched converter must exist first:
#   git -C /home/fsanches/compartilhado/babelfont-rs-worktrees/integration-ff-prs worktree add \
#       --detach /home/fsanches/compartilhado/sfd-reland-scratch/heights/bf-altuni 17ea899
#   git -C .../bf-altuni apply <this dir>/babelfont-altuni-lookup.patch
#   (cd .../bf-altuni && CARGO_BUILD_JOBS=3 CARGO_TARGET_DIR=/home/fsanches/compartilhado/sfd-reland-scratch/heights/bf-target \
#       cargo build --release -p babelfont --features cli)
#
# Run: bash rerun.sh probes | builds
set -uo pipefail
P=$(cd "$(dirname "$0")" && pwd); R=$P/../runs
PY=/home/fsanches/compartilhado/gftools/venv/bin/python3
BF0=/home/fsanches/compartilhado/babelfont-rs-worktrees/integration-ff-prs/target-heights/release/babelfont
BF1=/home/fsanches/compartilhado/sfd-reland-scratch/heights/bf-target/release/babelfont
case ${1:-} in
  probes)
    "$PY" "$P/facts.py" > "$R/facts.txt"
    "$PY" "$P/hypotheses.py" > "$R/hypotheses.txt"
    for s in KottaOne-Regular Macondo-Regular Rosarivo-Italic; do "$PY" "$P/hypotheses.py" dump $s > "$R/dump-$s.txt"; done
    "$PY" "$P/provenance.py" > "$R/provenance.txt"
    "$PY" "$P/ledger_release_history.py" > "$R/ledger_release_history.txt"
    "$PY" "$P/otf_bluevalues.py" Ledger-Regular LilitaOne-Regular Lustria-Regular Magra-Bold MergeOne-Regular \
        OleoScript-Bold OleoScript-Regular OleoScriptSwashCaps-Bold OleoScriptSwashCaps-Regular Rambla-Bold \
        Rambla-BoldItalic Sail-Regular TextMeOne-Regular > "$R/otf_bluevalues.tsv"
    bash "$P/make_edits.sh" > "$R/make_edits.txt" ;;
  builds)
    U16="KottaOne-Regular Ledger-Regular LilitaOne-Regular Lustria-Regular Macondo-Regular Magra-Bold MergeOne-Regular OleoScript-Bold OleoScript-Regular OleoScriptSwashCaps-Bold OleoScriptSwashCaps-Regular Rambla-Bold Rambla-BoldItalic Rosarivo-Italic Sail-Regular TextMeOne-Regular"
    for set_ in before altuni blues final; do bash "$P/runs.sh" $set_ > "$R/$set_.log" 2>&1; done
    # the four CLEAN siblings must stay CLEAN under the fixed converter
    bash "$P/runs.sh" altuni Magra-Regular Rambla-Italic Rambla-Regular Rosarivo-Regular >> "$R/altuni.log" 2>&1
    W5="Magra-Bold OleoScript-Bold OleoScriptSwashCaps-Bold Rambla-Bold Rambla-BoldItalic"
    bash "$P/gate_with_workarounds.sh" blues $W5; bash "$P/gate_with_workarounds.sh" final $W5
    bash "$P/nothing_else_opened.sh" before blues $U16 > "$R/nothing_else_opened-before-blues.txt"
    bash "$P/nothing_else_opened.sh" before altuni $U16 > "$R/nothing_else_opened-before-altuni.txt"
    bash "$P/nothing_else_opened.sh" before final $U16 > "$R/nothing_else_opened-before-final.txt"
    "$PY" "$P/altuni_regression.py" "$BF0" "$BF1" > "$R/altuni_regression.txt" ;;
  *) echo "usage: rerun.sh probes|builds" >&2; exit 2 ;;
esac
