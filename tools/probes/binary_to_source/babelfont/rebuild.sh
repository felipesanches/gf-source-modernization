#!/bin/sh
# Rebuild the babelfont binary the binary_to_source measurements ran with.
#
# It is simoncozens/babelfont-rs main at 3dabb000 plus three branches that were not
# public when measured: sr-aef-uncompile-fixes and ttf-static-font-fidelity (the patch
# series beside this script, for review), and typographic-family-names (pr-bodies/
# babelfont-typographic-family-names.md), merged as one tree: measure-integration.diff.
# The script checks that the applied tree is the measured one: the SHA-256 of its file
# listing (`git ls-files -s`: mode, blob and path of every file).
#
#   sh rebuild.sh <empty scratch dir>      -> <dir>/target/release/babelfont
set -eu
D=${1:?scratch directory}
HERE=$(cd "$(dirname "$0")" && pwd)
git clone -q https://github.com/simoncozens/babelfont-rs "$D/babelfont-rs"
cd "$D/babelfont-rs"
git checkout -q 3dabb000
git apply --index --binary "$HERE/measure-integration.diff"
SUM=$(git ls-files -s | sha256sum | cut -d' ' -f1)
[ "$SUM" = 2fa0ccc1b78ef888f93d509b9f0b6d0ba79058fa8b9641ca835b74df09959d9a ] || { echo "the applied tree is not the measured one"; exit 1; }
CARGO_TARGET_DIR="$D/target" cargo build --release -q -p babelfont --features cli
echo "$D/target/release/babelfont"
