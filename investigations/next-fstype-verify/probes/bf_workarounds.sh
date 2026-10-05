#!/bin/bash
# bf_workarounds.sh -- the converter step as tools/land.py runs it (verification copy).
#
# Question answered: with the same converter and flags tools/baseline.sh passes, plus
# tools/workarounds.apply_all(<out.glyphs>, <in.sfd>) -- the call land.py's convert()
# makes right after babelfont -- which gate rows remain? Pass as BF= to baseline.sh.
# REAL_BF defaults to babelfont-rs integration-ff-prs 17ea899 (target-heights build).
set -euo pipefail
REAL_BF=${REAL_BF:-/home/fsanches/compartilhado/babelfont-rs-worktrees/integration-ff-prs/target-heights/release/babelfont}
"$REAL_BF" "$@"
/home/fsanches/compartilhado/gftools/venv/bin/python3 -c "
import sys; sys.path.insert(0, '/home/fsanches/compartilhado/gf-source-modernization/tools')
import workarounds
for n in workarounds.apply_all(sys.argv[2], sys.argv[1]): print('workaround:', n)
" "$1" "$2"
