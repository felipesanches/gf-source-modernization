#!/bin/sh
# Usage: cmp_added.sh <orig-commit> <worktree> [<new-rev-or-empty-for-worktree>]
# Compares the added/removed lines (leading whitespace stripped, sorted) of the
# original commit with those of the ported change (working tree vs HEAD, or a commit).
O=$1; D=$2; N=${3:-}
G=/home/fsanches/compartilhado/babelfont-rs-worktrees/gf-sfd-conversion
git -C $G show --format= $O | /usr/bin/grep -E '^[+-]' | /usr/bin/grep -vE '^(\+\+\+|---) ' | sed -E 's/^([+-])[[:space:]]*/\1/' | sort > /home/fsanches/compartilhado/babelfont-rs-worktrees/port-496e904-work/cmp.orig
if [ -n "$N" ]; then git -C $D show --format= $N; else git -C $D diff HEAD; fi | /usr/bin/grep -E '^[+-]' | /usr/bin/grep -vE '^(\+\+\+|---) ' | sed -E 's/^([+-])[[:space:]]*/\1/' | sort > /home/fsanches/compartilhado/babelfont-rs-worktrees/port-496e904-work/cmp.new
diff /home/fsanches/compartilhado/babelfont-rs-worktrees/port-496e904-work/cmp.orig /home/fsanches/compartilhado/babelfont-rs-worktrees/port-496e904-work/cmp.new && echo "IDENTICAL (modulo indentation and position)"
