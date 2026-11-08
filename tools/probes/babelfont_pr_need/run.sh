#!/bin/sh
# Question answered: which of the open babelfont-rs PR branches does any genuine FontForge
# original (not a -TTF.sfd import of the binaries, P13) still need? Each converter = Simon's
# main + ONE branch merged (u0 = main alone); the six originals land on each, into scratch.
# Usage: sh run.sh            (scratch: ~/compartilhado/tmp/bf-pr-need-2026-11-08)
#        BRANCHES="a+b" REPOS="thabit" sh run.sh   (combined converters, a subset of repos)
set -u
S=/home/fsanches/compartilhado/tmp/bf-pr-need-2026-11-08
W=/home/fsanches/compartilhado/gf-source-modernization
BF=/home/fsanches/compartilhado/babelfont-rs
PY=/home/fsanches/compartilhado/gftools/venv/bin/python3
BASE=925bb242
REPOS="${REPOS:-comicrelief thabit lohitbengali lohittamil kristi novamono}"
BRANCHES="${BRANCHES:-u0 fontforge-shadowed-kern-pairs fontforge-legacy-os2-version fontforge-spacing-marks fontforge-ligature-anchors fontforge-notdef fontforge-fixed-pitch glyphs3-localized-name-entries fontforge-no-anchor-propagation fontforge-ligature-carets fontforge-gdef-classes typographic-family-names}"
mkdir -p "$S"
table_of() { for t in families.tsv families-next.tsv; do awk -F'\t' -v r="$1" 'NR>1 && $1==r {f=1} END{exit !f}' "$W/$t" && { echo "$W/$t"; return; }; done; }
for b in $BRANCHES; do
  wt="$S/wt-$b"; log="$S/logs-$b"; mkdir -p "$log"
  echo "== $b $(date -Is)" >> "$S/progress.txt"
  if [ ! -d "$wt" ]; then
    git -C "$BF" worktree add -q --detach "$wt" "$BASE" || { echo "   worktree failed" >> "$S/progress.txt"; continue; }
    if [ "$b" != u0 ]; then
      # a+b merges several branches (a combined converter)
      ok=1; for part in $(echo "$b" | tr '+' ' '); do
        git -C "$wt" -c user.name=measure -c user.email=measure@localhost merge -q --no-edit "$part" >> "$S/progress.txt" 2>&1 || { ok=0; break; }
      done
      [ "$ok" = 1 ] || { echo "   merge failed" >> "$S/progress.txt"; continue; }
    fi
  fi
  sudo -n /usr/local/sbin/drop-caches 2>/dev/null || true
  BF_TREE="$wt" sh "$W/tools/build_babelfont.sh" > "$log/build.txt" 2>&1 || { echo "   build failed" >> "$S/progress.txt"; continue; }
  for r in $REPOS; do
    BF_TREE="$wt" OUT="$S/repos-$b" LANDED="$S/landed-$b.tsv" SCRATCH="$S/scratch" FAMILIES="$(table_of $r)" \
      "$PY" "$W/tools/land.py" "$r" --rebuild --unpublished-converter > "$log/$r.log" 2>&1
    echo "   $r rc=$? $(head -n 1 "$log/$r.log" | cut -c1-160)" >> "$S/progress.txt"
  done
  rm -rf -- "${wt:?}/target-heights/release/build" "${wt:?}/target-heights/release/deps" "${wt:?}/target-heights/release/incremental"
  df -h /home/fsanches/compartilhado | tail -1 >> "$S/progress.txt"
done
echo "done $(date -Is)" >> "$S/progress.txt"
