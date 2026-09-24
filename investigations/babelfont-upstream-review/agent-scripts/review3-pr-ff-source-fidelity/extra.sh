#!/bin/bash
# Base tests, cargo doc warnings (base and HEAD), mutation check of the snap tests against the round-2 filter.
S=/tmp/claude-1000/-home-fsanches-compartilhado-GoogleFonts/f55394dc-b840-4055-b5b4-e2463e4b4dd8/scratchpad/review3-pr-ff-source-fidelity
R=/home/fsanches/compartilhado/babelfont-rs-worktrees/pr-ff-source-fidelity
X=/home/fsanches/compartilhado/babelfont-rs-worktrees/target-review3-pr-ff-source-fidelity/export
export CARGO_TARGET_DIR=/home/fsanches/compartilhado/babelfont-rs-worktrees/target-review3-pr-ff-source-fidelity CARGO_BUILD_JOBS=3
sudo -n /usr/local/sbin/drop-caches
rm -rf $X; mkdir -p $X; git -C $R archive upstream/main | tar -x -m -C $X
(cd $X && cargo test -p babelfont --no-fail-fast > $S/base-test.log 2>&1; echo "rc=$?" >> $S/base-test.log)
(cd $X && cargo doc -p babelfont --no-deps > $S/base-doc.log 2>&1; echo "rc=$?" >> $S/base-doc.log)
sudo -n /usr/local/sbin/drop-caches
(cd $R && cargo doc -p babelfont --no-deps > $S/head-doc.log 2>&1; echo "rc=$?" >> $S/head-doc.log)
# Mutation: HEAD tree, with the round-2 filter body (tests from HEAD).
rm -rf $X; mkdir -p $X; git -C $R archive HEAD | tar -x -m -C $X
python3 - "$R" "$X" <<'PY'
import subprocess, sys
R, X = sys.argv[1], sys.argv[2]
old = subprocess.check_output(['git','-C',R,'show','9053387:babelfont/src/filters/snapcomponenttransforms.rs'], text=True)
new = open(f'{X}/babelfont/src/filters/snapcomponenttransforms.rs').read()
old_code = old.split('#[allow(clippy::unwrap_used, clippy::expect_used)]\n#[cfg(test)]')[0]
new_tests = '#[allow(clippy::unwrap_used, clippy::expect_used)]\n#[cfg(test)]' + new.split('#[allow(clippy::unwrap_used, clippy::expect_used)]\n#[cfg(test)]')[1]
# tests need Layer and Component in scope
old_code = old_code.replace('use crate::shape::Shape;', 'use crate::shape::{Component, Shape};\n#[allow(unused_imports)]\nuse crate::Layer;')
open(f'{X}/babelfont/src/filters/snapcomponenttransforms.rs','w').write(old_code + new_tests)
PY
(cd $X && cargo test -p babelfont --lib snapcomponenttransforms > $S/mut-test.log 2>&1; echo "rc=$?" >> $S/mut-test.log)
echo done > $S/extra.done
