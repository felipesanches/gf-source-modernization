#!/bin/sh
# Question answered: do these landed repositories still land CLEAN when re-landed with the
# same converter, after a change to what the landing writes (e.g. the template)? Each repo is
# re-landed (land.py --rebuild, into the real OUT and landed.tsv) with the babelfont revision its
# current convert commit names, so only the change under test differs.
# Usage: sh tools/reland/reland_same_converter.sh <logs dir> <repo>...   (one land job at a time;
# do not edit this workspace while it runs: the landings cite its HEAD)
set -u
W=/home/fsanches/compartilhado/gf-source-modernization
R=/home/fsanches/compartilhado/sfd-reland-repos
LOGS=${1:?logs dir}; shift
export FAMILIES=$W/families-binary.tsv
export TMPDIR=/home/fsanches/compartilhado/tmp
mkdir -p "$LOGS"
for repo in "$@"; do
    rev=$(git -C "$R/$repo" log --format=%s | grep -oE 'babelfont [0-9a-f]{7,}' | head -1 | cut -d' ' -f2)
    case "$rev" in
        26fdcfa*) tree=/home/fsanches/compartilhado/babelfont-rs-worktrees/2026-11-02 ;;
        d7f67ca*) tree=/home/fsanches/compartilhado/babelfont-rs-worktrees/upstream-main ;;
        *) echo "$repo: SKIPPED -- converter ${rev:-?} has no tree here"; continue ;;
    esac
    BF_TREE=$tree /home/fsanches/compartilhado/gftools/venv/bin/python3 -I "$W/tools/land.py" "$repo" --rebuild > "$LOGS/$repo.log" 2>&1
    grep -E "^$repo: " "$LOGS/$repo.log" | tail -1
done | tee "$LOGS/summary.txt"
echo done
