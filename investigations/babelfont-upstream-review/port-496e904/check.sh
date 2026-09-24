#!/bin/sh
# Usage: check.sh <worktree-dir> <target-name> <log-prefix>
# Runs fmt --check, clippy (default and --features cli) and cargo test -p babelfont
# for one worktree, writing logs to <log-prefix>.{fmt,clippy,clippy-cli,test}.log
set -u
D=$1; T=$2; L=$3
export CARGO_TARGET_DIR=/home/fsanches/compartilhado/babelfont-rs-worktrees/port-496e904-work/target-$T
export CARGO_BUILD_JOBS=4
cd "$D" || exit 1
df -h /home/fsanches/compartilhado | tail -1
sudo -n /usr/local/sbin/drop-caches
echo "HEAD $(git rev-parse --short HEAD)" > "$L.head"
cargo fmt --all -- --check > "$L.fmt.log" 2>&1; echo "fmt rc=$?" >> "$L.fmt.log"
cargo clippy --all-targets > "$L.clippy.log" 2>&1; echo "clippy rc=$?" >> "$L.clippy.log"
sudo -n /usr/local/sbin/drop-caches
cargo clippy -p babelfont --all-targets --features cli > "$L.clippy-cli.log" 2>&1; echo "clippy-cli rc=$?" >> "$L.clippy-cli.log"
sudo -n /usr/local/sbin/drop-caches
cargo test -p babelfont --no-fail-fast > "$L.test.log" 2>&1; echo "test rc=$?" >> "$L.test.log"
echo DONE > "$L.done"
