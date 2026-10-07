#!/bin/sh
# Question answered: once the gftools-rust productionNames change is merged, are the 42
# repositories of google/fonts#11077 ready to push with it?
#
#   sh tools/production_names_finalize.sh <merged gftools-rust revision>
#
# 1. pins tools/land.py (B3_ID) and the template CI (GFTOOLS_RUST_REV) to that revision, and
#    commits that here;
# 2. builds gftools-builder at that revision into land.B3_DEFAULT;
# 3. replaces each repository's provisional "Builder config:" commit (tools/rekey.py --redo),
#    rebuilt and gated with the published builder;
# 4. runs tools/push.sh --check and tools/check_publishable.py over the 42.
# Pushing stays a separate, human step (tools/push.sh), and so does the google/fonts PR
# (tools/metadata.py <branch> <repo>... after the push).
set -eu
REV=${1:?merged simoncozens/gftools-rust revision}
W=$(cd "$(dirname "$0")/.." && pwd)
C=/home/fsanches/compartilhado
PY=$C/gftools/venv/bin/python3
REPOS=$(cat "$W/push-2026-10-03.txt")
git -C "$C/gftools-rust" fetch -q origin
git -C "$C/gftools-rust" merge-base --is-ancestor "$REV" origin/main ||
  { echo "FATAL: $REV is not on simoncozens/gftools-rust main"; exit 1; }
REV=$(git -C "$C/gftools-rust" rev-parse --short=7 "$REV")

# 1. the pin: the builder revision, and the fontc its Cargo.lock locks (commit messages state both)
FONTC=$(git -C "$C/gftools-rust" show "$REV:Cargo.lock" | grep -A1 '^name = "fontc"$' | sed -n 's/^version = "\(.*\)"$/\1/p')
[ -n "$FONTC" ] || { echo "FATAL: no fontc in $REV's Cargo.lock"; exit 1; }
sed -i "s/^B3_ID, FONTC_ID = \"[0-9a-f]*\", \"[^\"]*\"/B3_ID, FONTC_ID = \"$REV\", \"$FONTC\"/" "$W/tools/land.py"
grep -q "^B3_ID, FONTC_ID = \"$REV\", \"$FONTC\"" "$W/tools/land.py" || { echo "FATAL: land.py pin not updated"; exit 1; }
sed -i "s/GFTOOLS_RUST_REV: [0-9a-f]*/GFTOOLS_RUST_REV: $REV/" "$W/templates/ufr-template/.github/workflows/build.yaml"
git -C "$W" add tools/land.py templates/ufr-template/.github/workflows/build.yaml
git -C "$W" commit -q -m "Pin gftools-rust $REV (productionNames)

Assisted by an AI agent (Claude Opus 5.5)"

# 2. the builder, where land.py looks for it
WT=$C/tmp/gftools-rust-at-$REV
[ -d "$WT" ] || git -C "$C/gftools-rust" worktree add -q --detach "$WT" "$REV"
( cd "$WT" && CARGO_TARGET_DIR=$C/tmp/gftools-rust-target cargo build --release -q -p gftools-builder )

# 3. the real commits
( cd "$W" && "$PY" tools/rekey.py --redo $REPOS )

# 4. the checks
( cd "$W" && sh tools/push.sh --check $REPOS )
set --
for r in $REPOS; do set -- "$@" "$C/sfd-reland-repos/$r:origin/main..HEAD"; done
( cd "$W" && python3 tools/check_publishable.py --fetch "$@" )
