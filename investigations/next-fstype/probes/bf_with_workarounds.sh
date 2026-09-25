#!/bin/bash
# bf_with_workarounds.sh -- the converter step exactly as tools/land.py runs it.
#
# Question answered: with the SAME converter and flags tools/baseline.sh uses, and the
# named toolchain workarounds tools/land.py applies inside the convert commit
# (tools/workarounds.py: usWeightClass from the .sfd's TTFWeight as FEA, because
# fontc ignores a single-master Glyphs instance's weightClass; the fractional italic
# angle), which table rows still block?
#
# tools/baseline.sh deliberately measures the converter alone, so every usWeightClass
# row it reports for a non-400 style is that known fontc gap. land.py closes it from
# the .sfd; this wrapper lets the unchanged baseline.sh harness measure the same thing
# without editing a shared tool: pass it as BF=.
#
#   BF=investigations/next-fstype/probes/bf_with_workarounds.sh \
#   FAMILIES=... OUT=... TAG=... SCRATCH=... bash tools/baseline.sh <Style>
#
# baseline.sh calls "$BF" <in.sfd> <out.glyphs> <flags...>; this runs the real
# converter (REAL_BF, default: babelfont-rs integration-ff-prs = upstream main 496e904
# + PRs #91/#92/#93) with the same arguments, then workarounds.apply_all(out, in) and
# prints what fired (it lands in the .gate.txt log).
set -euo pipefail
W=/home/fsanches/compartilhado/sfd-reland
REAL_BF=${REAL_BF:-/home/fsanches/compartilhado/babelfont-rs-worktrees/integration-ff-prs/target-heights/release/babelfont}
PY=/home/fsanches/compartilhado/gftools/venv/bin/python3
"$REAL_BF" "$@"
"$PY" "$W/tools/workarounds.py" "$2" "$1" | sed 's/^/workaround: /'
