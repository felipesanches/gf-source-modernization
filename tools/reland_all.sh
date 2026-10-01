#!/bin/sh
# Question answered: with the converter and builder now fully upstream (babelfont main,
# gftools-rust), how many landed repositories pass the table gate, exact codepoints AND the
# functional gate?
#
# Re-lands every repository of families.tsv and families-next.tsv with tools/land.py
# --rebuild (the previous generation is kept as <repo>.prev), one at a time, and logs each
# run to logs/reland-<tag>/<repo>.log; the verdict line of each lands in landed.tsv.
#
# Usage: BF_TREE=<babelfont upstream worktree> sh tools/reland_all.sh <tag> [repo ...]
set -u
W=$(cd "$(dirname "$0")/.." && pwd)
PY=${PY:-/home/fsanches/compartilhado/gftools/venv/bin/python3}
TAG=$1; shift
LOG="$W/logs/reland-$TAG"
mkdir -p "$LOG"
repos_of() { awk -F'\t' 'NR>1 && $1!="" {print $1}' "$1" | sort -u; }
run() {  # $1 = pairing table, $2 = repo
  echo "== $2 ($(basename "$1")) $(date -Is)" >> "$LOG/progress.txt"
  FAMILIES="$1" "$PY" "$W/tools/land.py" "$2" --rebuild ${LAND_ARGS:-} > "$LOG/$2.log" 2>&1
  echo "   rc=$? $(tail -n 1 "${LANDED:-$W/landed.tsv}" | cut -f1,5)" >> "$LOG/progress.txt"
  df -h /home/fsanches/compartilhado | tail -1 >> "$LOG/progress.txt"
}
for t in families.tsv families-next.tsv; do
  for r in $(repos_of "$W/$t"); do
    if [ $# -gt 0 ]; then case " $* " in *" $r "*) ;; *) continue ;; esac; fi
    run "$W/$t" "$r"
  done
done
echo "done $(date -Is)" >> "$LOG/progress.txt"
