#!/bin/sh
# Differential check of babelfont-rs PR #95: b4dc853 (deferred override) vs
# 8042926 (sfntRevision parsed straight into font.version). See README.md.
set -eu
REPO=/home/fsanches/compartilhado/babelfont-rs-worktrees/fix-fontforge-sfnt-revision
OUT=${OUT:-/home/fsanches/compartilhado/sfd-reland-scratch/pr95/review}
HERE=$(cd "$(dirname "$0")" && pwd)
BASE=/home/fsanches/compartilhado/
export CARGO_TARGET_DIR=${CARGO_TARGET_DIR:-/home/fsanches/compartilhado/sfd-reland-scratch/pr95/target-review}
export CARGO_BUILD_JOBS=${CARGO_BUILD_JOBS:-3}
mkdir -p "$OUT"
# Corpus: every unique (by content) .sfd under these directories.
(cd $BASE && find sfd-batch5-repos sfd-batch6-repos sfd-reland-repos sfd-batch2 sfd-batch7 \
    sfd-func-audit debian-fonts-research -name '*.sfd' -not -path '*/.git/*' -print0 2>/dev/null \
  | xargs -0 sha1sum | sort -k1,1 -u | cut -c43-) > "$OUT/sfd-uniq.txt"
for c in b4dc853 8042926; do
  rm -rf "$OUT/tree-$c"; mkdir -p "$OUT/tree-$c"
  git -C "$REPO" archive $c | tar -x -C "$OUT/tree-$c"
  cat "$HERE/harness.rs" >> "$OUT/tree-$c/babelfont/src/convertors/fontforge/tests.rs"
  # git archive keeps commit-time mtimes; cargo would reuse a stale build without this.
  find "$OUT/tree-$c" -type f -name '*.rs' -exec touch {} +
  sudo -n /usr/local/sbin/drop-caches || true
  (cd "$OUT/tree-$c" && REVIEW_DUMP="$OUT/dump-$c.txt" REVIEW_CORPUS="$OUT/sfd-uniq.txt" \
     REVIEW_CORPUS_BASE=$BASE cargo test -p babelfont --lib convertors::fontforge::tests::zz_review_dump)
done
python3 "$HERE/compare.py" "$OUT"
