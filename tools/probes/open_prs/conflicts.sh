#!/bin/sh
# Question answered: which open PR heads of a GitHub repository, and which local branches,
# merge with the repository's main without a conflict?
# Usage: sh conflicts.sh <local clone> <owner/repo> [<local branch>...]
# Reads the PR heads over git (no API quota); prints "<ref> <head> clean|CONFLICT(<files>)".
# A PR already contained in main is skipped (a squash-merged PR still shows a conflict:
# read it against the open list). git merge-tree --write-tree exits 0 clean, 1 conflict.
set -u
C=${1:?clone}; R=${2:?owner/repo}; shift 2
git -C "$C" fetch -q "https://github.com/"$R".git" main '+refs/pull/*/head:refs/remotes/pr-probe/*'
main=$(git -C "$C" rev-parse FETCH_HEAD)
echo "main $(git -C "$C" rev-parse --short=8 "$main")"
check() {
    out=$(git -C "$C" merge-tree --write-tree --name-only --no-messages "$main" "$1"); rc=$?
    case $rc in
        0) echo clean ;;
        1) echo "CONFLICT($(echo "$out" | tail -n +2 | sort -u | tr '\n' ' ' | sed 's/ $//'))" ;;
        *) echo "ERROR($rc)" ;;
    esac
}
for n in $(git -C "$C" for-each-ref --format='%(refname:lstrip=3)' refs/remotes/pr-probe/ | sort -n); do
    h=refs/remotes/pr-probe/$n
    git -C "$C" merge-base --is-ancestor "$h" "$main" && continue
    echo "#$n $(git -C "$C" rev-parse --short=8 "$h") $(check "$h")"
done
for b in "$@"; do echo "$b $(git -C "$C" rev-parse --short=8 "$b") $(check "$b")"; done
