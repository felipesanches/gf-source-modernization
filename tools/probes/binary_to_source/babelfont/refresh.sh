#!/bin/sh
# Refresh this directory from the babelfont branches after a converter change: the two patch
# series (for review), measure-integration.diff (the measured tree as one diff on public
# upstream $BASE) and the SHA-256 that rebuild.sh checks; then verify that the diff
# applied to $BASE gives exactly the measured tree. $BASE is the upstream commit the
# branches are rebased on; rebuild.sh checks out the same one.
#
#   sh refresh.sh        (no arguments; paths are those of this workstation)
set -eu
HERE=$(cd "$(dirname "$0")" && pwd)
B=/home/fsanches/compartilhado/babelfont-rs
MEASURE=/home/fsanches/compartilhado/babelfont-rs-worktrees/ttf-measure
CHECK=/home/fsanches/compartilhado/tmp/babelfont-apply-check
BASE=d44f2bdc
for series in sr-aef-uncompile-fixes ttf-static-font-fidelity glyphs3-localized-name-entries \
    fontforge-fixed-pitch ttf-post-fixed-pitch; do
  mkdir -p "$HERE/$series"
  find "${HERE:?}/${series:?}" -maxdepth 1 -type f -name '*.patch' -delete
done
git -C "$B" format-patch -q --zero-commit --no-signature -o "$HERE/sr-aef-uncompile-fixes" \
  upstream/main..sr-aef-uncompile-fixes
git -C "$B" format-patch -q --zero-commit --no-signature -o "$HERE/ttf-static-font-fidelity" \
  sr-aef-uncompile-fixes..ttf-static-font-fidelity
git -C "$B" format-patch -q --zero-commit --no-signature -o "$HERE/glyphs3-localized-name-entries" \
  upstream/main..glyphs3-localized-name-entries
git -C "$B" format-patch -q --zero-commit --no-signature -o "$HERE/fontforge-fixed-pitch" \
  upstream/main..fontforge-fixed-pitch
git -C "$B" format-patch -q --zero-commit --no-signature --no-merges -o "$HERE/ttf-post-fixed-pitch" \
  ttf-post-fixed-pitch ^ttf-static-font-fidelity ^fontforge-fixed-pitch
git -C "$B" diff --binary "$BASE" ttf-measure > "$HERE/measure-integration.diff"
SUM=$(git -C "$MEASURE" ls-files -s | sha256sum | cut -d' ' -f1)
sed -i "s/\[ \"\$SUM\" = [0-9a-f]\{64\} \]/[ \"\$SUM\" = $SUM ]/" "$HERE/rebuild.sh"
grep -q "$SUM" "$HERE/rebuild.sh"
git -C "$B" worktree add -q --detach "$CHECK" "$BASE"
git -C "$CHECK" apply --index --binary "$HERE/measure-integration.diff"
GOT=$(git -C "$CHECK" ls-files -s | sha256sum | cut -d' ' -f1)
git -C "$B" worktree remove --force "$CHECK"
git -C "$B" worktree prune
[ "$GOT" = "$SUM" ] || { echo "the diff does not reproduce the measured tree"; exit 1; }
echo "$(ls "$HERE"/*/*.patch | wc -l) patches in $(ls -d "$HERE"/*/ | wc -l) series; the diff reproduces the measured tree"
