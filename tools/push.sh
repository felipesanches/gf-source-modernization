#!/bin/sh
# Push the landed repositories. For Felipe: this environment has no GitHub
# credentials, so nothing here has been pushed.
#
#   sh tools/push.sh --check        report, change nothing (run this first)
#   sh tools/push.sh                push every repository that --check calls READY
#   sh tools/push.sh lekton kristi  just these
#
# Reads landed.tsv (the last row per repository wins) and, for each repository:
#   - refuses unless the babelfont revision its convert commit cites is on
#     simoncozens/babelfont-rs main (a font repo must never depend on a fork)
#   - refuses unless tools/verify_landed.py passes for it (re-run here, so a
#     repository edited after landing cannot slip through)
#   - an EMPTY googlefonts/<repo> (a fresh repository): pushes `main`
#   - a fork: pushes the branch and prints the compare URL for the pull request
#   - never force-pushes; refuses if the remote branch exists and is not an
#     ancestor of the local one
# Every push is logged to push_log.tsv.
set -u
W=$(cd "$(dirname "$0")/.." && pwd)
R=/home/fsanches/compartilhado/sfd-reland-repos
PY=/home/fsanches/compartilhado/gftools/venv/bin/python3
BF_TREE=${BF_TREE:-/home/fsanches/compartilhado/babelfont-rs-worktrees/gf-sfd-conversion}   # any worktree of babelfont-rs
git -C "$BF_TREE" fetch -q upstream main || { echo "cannot fetch babelfont upstream"; exit 1; }
CHECK=
[ "${1:-}" = "--check" ] && { CHECK=1; shift; }

repos="$*"
[ -n "$repos" ] || repos=$(awk -F'\t' '{print $1}' "$W/landed.tsv" | awk '!seen[$0]++')

for repo in $repos; do
  row=$(awk -F'\t' -v r="$repo" '$1==r' "$W/landed.tsv" | tail -1)
  [ -n "$row" ] || { echo "$repo: not landed"; continue; }
  branch=$(echo "$row" | cut -f2); status=$(echo "$row" | cut -f5)
  d="$R/$repo"
  head=$(git -C "$d" rev-parse --short HEAD 2>/dev/null)
  url=$(git -C "$d" remote get-url origin 2>/dev/null)
  if [ "$status" != CLEAN ]; then
    echo "$repo: NOT READY -- landed $status ($(echo "$row" | cut -f6))"; continue
  fi
  remote=$(GIT_TERMINAL_PROMPT=0 git ls-remote "$url" "refs/heads/$branch" 2>/dev/null | cut -c1-40)
  if [ -n "$remote" ] && ! git -C "$d" merge-base --is-ancestor "$remote" HEAD 2>/dev/null; then
    echo "$repo: REFUSED -- $url $branch is at ${remote%"${remote#???????}"}, not an ancestor of $head (no force-push)"
    continue
  fi
  # the converter the convert commit cites must be merged upstream, never only in a fork
  rev=$(git -C "$d" log --format=%s | sed -n 's/^Convert to \.glyphs with babelfont \([0-9a-f]*\)$/\1/p' | head -1)
  if [ -z "$rev" ] || ! git -C "$BF_TREE" merge-base --is-ancestor "$rev" upstream/main 2>/dev/null; then
    echo "$repo: BLOCKED -- cites babelfont ${rev:-?}, not on simoncozens/babelfont-rs main; re-land after it merges"
    continue
  fi
  fam="$W/families.tsv"
  grep -q "^$repo	" "$fam" || fam="$W/families-next.tsv"   # the table that pairs this repo
  if ! FAMILIES="$fam" "$PY" "$W/tools/verify_landed.py" "$repo" >/dev/null 2>&1; then
    echo "$repo: REFUSED -- verify_landed.py fails; run it to see why"; continue
  fi
  case "$url" in
    */googlefonts/*) ;;
    *) echo "$repo: HOLD -- origin is $url, not a googlefonts repository (decision needed)"; continue ;;
  esac
  if [ -n "$CHECK" ]; then
    echo "$repo: READY  $head -> $url $branch${remote:+ (fast-forward from ${remote%"${remote#???????}"})}"
    continue
  fi
  if git -C "$d" push origin "$branch"; then
    printf '%s\t%s\t%s\t%s\n' "$repo" "$branch" "$head" "$url" >> "$W/push_log.tsv"
    if [ "$branch" != main ]; then
      echo "$repo: pushed $branch -- open the pull request:"
      echo "    ${url%.git}/compare/master...$branch?expand=1"
      echo "    body: $W/pr-bodies/$repo.md"
    else
      echo "$repo: pushed main"
    fi
  else
    echo "$repo: PUSH FAILED"
  fi
done
