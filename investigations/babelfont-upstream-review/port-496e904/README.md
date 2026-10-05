# Port of pr-ff-* onto simoncozens/babelfont-rs main 496e904 (2026-09-24)

Scratch workdir for rebasing pr-ff-reader-fixes, pr-ff-source-fidelity and
pr-ff-os2-defaults from 0b55947 onto 496e904 (da97d82 split fontforge.rs; its
`mod tests` became fontforge/tests.rs, de-indented by four spaces).

| script | question it answers | command |
|---|---|---|
| `split_hunks.py` | which hunks of an old commit's fontforge.rs diff are code and which are inside the old `mod tests`? writes `hunks/<c>.code.patch` (git apply) and `hunks/<c>.tests.rs` (added test lines, dedented) | `python3 split_hunks.py <repo> <commit> hunks` |
| `cmp_added.sh` | does a ported commit add/remove exactly the lines the original did (leading whitespace ignored, position ignored)? prints IDENTICAL | `sh cmp_added.sh <orig> <worktree> [<new>]` |
| `check.sh` | fmt --check, clippy --all-targets, clippy -p babelfont --all-targets --features cli, cargo test -p babelfont --no-fail-fast for one tree | `sh check.sh <dir> <target-name> <log-prefix>` |
| `check_commits.sh` | does every commit of a branch build, lint clean and test on its own? | `sh check_commits.sh <branch>` -> `logs/<branch>/<n>-<hash>.*.log` |
| `run_check_branch.sh` | re-runs gf-source-modernization's committed `tools/babelfont-upstream/check_branch.sh` for the three branches | `sh run_check_branch.sh` -> `logs/RESULT-<branch>.txt` |

Signal: the lib-unittest `test result:` line; the 11 failures must be exactly
`logs/upstream-496e904.failed.txt` (8 robocjk + 3 decomposecomponentreferences, untracked
noto-cjk-varco/notosanscjksc.rcjk fixture). `logs/merged-3way.*` is the three branches
merged together (256 passed, same 11 failed). `target-*` are regenerable cargo caches.
