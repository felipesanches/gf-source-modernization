#!/bin/sh
# Usage: check_commits.sh <branch>
# For every commit in upstream/main..<branch>, oldest first, checks it out in the
# detached scratch worktree wt-<branch> and runs check.sh on it (fmt --check,
# clippy --all-targets, clippy -p babelfont --all-targets --features cli,
# cargo test -p babelfont --no-fail-fast), with CARGO_TARGET_DIR target-<branch>.
# Logs: logs/<branch>/<n>-<shorthash>.{fmt,clippy,clippy-cli,test}.log
set -u
B=$1
W=/home/fsanches/compartilhado/babelfont-rs-worktrees/port-496e904-work
WT=$W/wt-$B
G=/home/fsanches/compartilhado/babelfont-rs-worktrees/gf-sfd-conversion
[ -d "$WT" ] || git -C $G worktree add --detach "$WT" upstream/main
mkdir -p $W/logs/$B
n=0
for c in $(git -C $G rev-list --reverse upstream/main..$B); do
  n=$((n+1))
  git -C "$WT" checkout -q --detach $c || exit 1
  $W/check.sh "$WT" $B $W/logs/$B/$n-$(git -C $G rev-parse --short $c)
done
echo ALLDONE > $W/logs/$B/ALLDONE
