#!/bin/sh
# Rebuild the babelfont binary the binary_to_source measurements ran with.
#
# It is simoncozens/babelfont-rs main at d44f2bdc plus four branches not merged when
# measured: sr-aef-uncompile-fixes and ttf-static-font-fidelity (patch series beside this
# script, for review), typographic-family-names (pr-bodies/
# babelfont-typographic-family-names.md) and glyphs3-localized-name-entries
# (simoncozens/babelfont-rs#117, series beside this script), merged as one tree:
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
[ "$SUM" = 5b4ce2ff69907f3467ee7ec0ddf9f94af24c9d8ffcaa35c23f6ca51f3d670738 ] || { echo "the applied tree is not the measured one"; exit 1; }
CARGO_TARGET_DIR="$D/target" cargo build --release -q -p babelfont --features cli
echo "$D/target/release/babelfont"
