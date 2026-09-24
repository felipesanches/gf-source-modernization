#!/bin/sh
# Review harness (disposable): does every commit of upstream/main..pr-ff-source-fidelity
# pass fmt --check, clippy --all-targets (default and -p babelfont --features cli) and
# cargo test -p babelfont --no-fail-fast on its own? Each commit is exported with
# git archive into a fresh tree (tar -m: fresh mtimes), built in one shared target dir.
# Output: pc-logs/<n>-<hash>.{fmt,clippy,clippy-cli,test}.log and pc-summary.txt
set -u
R=/home/fsanches/compartilhado/babelfont-rs-worktrees/port-496e904-work/review-pr-ff-source-fidelity
G=/home/fsanches/compartilhado/babelfont-rs-worktrees/pr-ff-source-fidelity
export CARGO_TARGET_DIR=$R/target-pc CARGO_BUILD_JOBS=3
mkdir -p $R/pc-logs
: > $R/pc-summary.txt
n=0
for c in $(git -C $G rev-list --reverse 496e904..24671e6); do
  n=$((n+1)); h=$(git -C $G rev-parse --short $c); L=$R/pc-logs/$n-$h
  rm -rf $R/pc-src; mkdir -p $R/pc-src
  git -C $G archive $c | tar -x -m -C $R/pc-src
  sudo -n /usr/local/sbin/drop-caches >/dev/null 2>&1 || true
  cd $R/pc-src || exit 1
  cargo fmt --all -- --check > $L.fmt.log 2>&1; f=$?
  cargo clippy --all-targets > $L.clippy.log 2>&1; c1=$?
  cargo clippy -p babelfont --all-targets --features cli > $L.clippy-cli.log 2>&1; c2=$?
  cargo test -p babelfont --no-fail-fast > $L.test.log 2>&1; t=$?
  w1=$(command grep -cE '^(warning|error)' $L.clippy.log); w2=$(command grep -cE '^(warning|error)' $L.clippy-cli.log)
  {
    echo "== $n $h fmt_rc=$f clippy_rc=$c1 warn=$w1 clippy_cli_rc=$c2 warn=$w2 test_rc=$t"
    command grep '^test result' $L.test.log | sed 's/finished in.*//'
    command grep ' \.\.\. FAILED$' $L.test.log | sort > $L.failed.txt
    echo "failed set == upstream 11: $(sort /home/fsanches/compartilhado/babelfont-rs-worktrees/port-496e904-work/logs/upstream-496e904.failed.txt | cmp -s $L.failed.txt - && echo yes || echo NO)"
  } >> $R/pc-summary.txt
done
echo ALLDONE >> $R/pc-summary.txt
