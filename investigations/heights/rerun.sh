#!/bin/bash
# Rerun every measurement quoted in FINDINGS.md (heights unit). One build at a time.
#   bash rerun.sh probes        # rule probes only (seconds)
#   bash rerun.sh builds        # harness runs (sequential, ~2 min each)
set -uo pipefail
H=$(cd "$(dirname "$0")" && pwd)
W=$(cd "$H/../.." && pwd)
PY=/home/fsanches/compartilhado/gftools/venv/bin/python3
ARC=/home/fsanches/compartilhado/upstream_repos/repo_archive/googlefonts/googlefontdirectory-hg.git
C=52f780bc9d197280a9f430574e179a5f233c56b6
# the stamped build of babelfont ca43adc (the height rule, not yet pinned); see FINDINGS
BFH=/home/fsanches/compartilhado/babelfont-rs-worktrees/gf-sfd-conversion/target-heights/release/babelfont
SCR=${SCRATCH:-/tmp/claude-1000/-home-fsanches-compartilhado-GoogleFonts/f55394dc-b840-4055-b5b4-e2463e4b4dd8/scratchpad/inv-heights}
export SCRATCH=$SCR
mkdir -p "$SCR/src" "$SCR/tree/patrickhand" "$H/edits"

src() {  # <family> <file> -> unmodified source in scratch
  git -C "$ARC" show "$C:ofl/$1/src/$2" > "$SCR/src/$2"
}

edit() { # <out.sfd> <in.sfd> <op> <args...>: a copy with one documented edit
  local out=$1 in=$2; shift 2
  cp "$in" "$out"
  "$PY" "$W/tools/sfd_edit.py" "$out" "$@"
}

if [ "${1:-}" = probes ]; then
  "$PY" "$H/ff_heights_probe.py" all > "$H/probe_all.txt"
  git -C "$ARC" archive "$C" ofl/patrickhand/src | tar -x -C "$SCR/tree/patrickhand" --strip-components=3
  for y in 2011 2012; do
    for s in HerrVonMuellerhoff-Regular-TTF:herrvonmuellerhoff Miama-Regular-TTF:miama \
             NosiferCaps-Regular-TTF:nosifercaps PatrickHand-Regular-TTF:patrickhand \
             UnifrakturCook-Bold-TTF:unifrakturcook; do
      f=${s%%:*}; fam=${s##*:}; src "$fam" "$f.sfd"
      "$PY" "$H/ff_heights_probe.py" dump "$SCR/src/$f.sfd" $y > "$H/dump-$f-$y.txt"
    done
  done
  "$PY" "$H/cff_heights_probe.py" "$SCR/tree/patrickhand/PatrickHand-Regular.otf" 2012 dump \
      > "$H/cff-PatrickHand-Regular.otf-2012.txt"
  # FFTM-selected vintage: 2011 rule when the release's FontForge predates 4d34d21ef866
  awk 'NR>1 { sel = ($2!="-" && $2<"2012-05-14") ? "2011" : "2012"; x = (sel=="2011")?$3:$4; c = (sel=="2011")?$6:$7; ok = (x==$5 && c==$8); m2 = ($4==$5 && $7==$8); n++; nok+=ok; nm+=m2; printf "%-27s %-10s sel=%s %s %s\n", $1, $2, sel, ok?"MATCH":"differ", ($0 ~ /states/)?"(stated)":"" } END { printf "vintage-selected rule reproduces %d of %d; master rule alone %d of %d\n", nok, n, nm, n }' "$H/probe_all.txt" > "$H/vintage_selection.txt"
  exit 0
fi

# --- harness runs ------------------------------------------------------------
src herrvonmuellerhoff HerrVonMuellerhoff-Regular-TTF.sfd
src miama Miama-Regular-TTF.sfd
src nosifercaps NosiferCaps-Regular-TTF.sfd
src patrickhand PatrickHand-Regular-TTF.sfd
src unifrakturcook UnifrakturCook-Bold-TTF.sfd

# stand-ins for the proposed converter change (FontForge < 4d34d21ef866 rule):
# the values the 2011 rule computes, stated in a copy of the source
e=$H/edits
edit "$e/HerrVonMuellerhoff-2011rule.sfd" "$SCR/src/HerrVonMuellerhoff-Regular-TTF.sfd" addfield OS2CapHeight 644
edit "$e/Miama-2011rule.sfd" "$SCR/src/Miama-Regular-TTF.sfd" addfield OS2XHeight 265
edit "$e/NosiferCaps-2011rule.sfd" "$SCR/src/NosiferCaps-Regular-TTF.sfd" addfield OS2XHeight 925
"$PY" "$W/tools/sfd_edit.py" "$e/NosiferCaps-2011rule.sfd" addfield OS2CapHeight 854
edit "$e/UnifrakturCook-2011rule.sfd" "$SCR/src/UnifrakturCook-Bold-TTF.sfd" addfield OS2XHeight 319
"$PY" "$W/tools/sfd_edit.py" "$e/UnifrakturCook-2011rule.sfd" addfield OS2CapHeight 485
# the proposed .sfd edit (provenance): PatrickHand's cap height
edit "$e/PatrickHand-capheight661.sfd" "$SCR/src/PatrickHand-Regular-TTF.sfd" addfield OS2CapHeight 661

run() { # <name> <style> [SRC_OVERRIDE] ; BF from the environment
  local name=$1 style=$2 ov=${3:-}
  TAG=heights OUT="$H/runs/$name" SRC_OVERRIDE="$ov" bash "$W/tools/baseline.sh" "$style"
}
for s in HerrVonMuellerhoff-Regular Miama-Regular NosiferCaps-Regular PatrickHand-Regular UnifrakturCook-Bold; do
  run before-f725e6a "$s"                     # pinned converter
  BF=$BFH run before-ca43adc "$s"             # + FontForge master height rule
done
BF=$BFH run after-ca43adc HerrVonMuellerhoff-Regular "$e/HerrVonMuellerhoff-2011rule.sfd"
BF=$BFH run after-ca43adc Miama-Regular "$e/Miama-2011rule.sfd"
BF=$BFH run after-ca43adc NosiferCaps-Regular "$e/NosiferCaps-2011rule.sfd"
BF=$BFH run after-ca43adc UnifrakturCook-Bold "$e/UnifrakturCook-2011rule.sfd"
BF=$BFH run after-ca43adc PatrickHand-Regular "$e/PatrickHand-capheight661.sfd"
