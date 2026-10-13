#!/bin/sh
# Rebuild the babelfont binary the binary_to_source measurements ran with.
#
# It is simoncozens/babelfont-rs main at d44f2bdc plus branches not merged when measured:
# sr-aef-uncompile-fixes, ttf-static-font-fidelity and ttf-post-fixed-pitch (the TTF reader),
# fontforge-fixed-pitch, glyphs3-localized-name-entries (simoncozens/babelfont-rs#117) --
# patch series beside this script, for review -- and typographic-family-names
# (pr-bodies/babelfont-typographic-family-names.md), merged as one tree:
# measure-integration.diff.
# The script checks that the applied tree is the measured one: the SHA-256 of its file
# listing (`git ls-files -s`: mode, blob and path of every file).
#
#   sh rebuild.sh <empty scratch dir>      -> <dir>/target/release/babelfont
set -eu
D=${1:?scratch directory}
HERE=$(cd "$(dirname "$0")" && pwd)
git clone -q https://github.com/simoncozens/babelfont-rs "$D/babelfont-rs"
cd "$D/babelfont-rs"
git checkout -q d44f2bdc
git apply --index --binary "$HERE/measure-integration.diff"
SUM=$(git ls-files -s | sha256sum | cut -d' ' -f1)
[ "$SUM" = b18ff003c317ee7d5f0c6cb88ae2107707610ccd4600043f69f095c9487fbbab ] || { echo "the applied tree is not the measured one"; exit 1; }
CARGO_TARGET_DIR="$D/target" cargo build --release -q -p babelfont --features cli
echo "$D/target/release/babelfont"
