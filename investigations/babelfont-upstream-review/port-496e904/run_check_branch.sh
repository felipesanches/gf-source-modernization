#!/bin/sh
# Re-runs gf-source-modernization's committed tools/babelfont-upstream/check_branch.sh for the three
# ported branches (base upstream/main 496e904), sharing one workdir so the base's cargo
# target dir is reused; output -> logs/RESULT-<branch>.txt
W=/home/fsanches/compartilhado/babelfont-rs-worktrees/port-496e904-work
for b in pr-ff-reader-fixes pr-ff-source-fidelity pr-ff-os2-defaults; do
  W=$W/check-branch sh /home/fsanches/compartilhado/gf-source-modernization/tools/babelfont-upstream/check_branch.sh $b > $W/logs/RESULT-$b.txt 2>&1
done
echo done > $W/logs/RESULT.done
