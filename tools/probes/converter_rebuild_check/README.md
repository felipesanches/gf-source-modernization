# Were the cited converters real builds of their trees?

On 2026-10-24 a CARGO_TARGET_DIR shared across babelfont-rs worktrees was found to replay one
worktree's compile for another (same unit hash, mtime freshness). The converters that landed
repositories cite were built in each worktree's own target-heights, seeded by copying another
worktree's `release/` directory; a fresh checkout is newer than the copied artifacts, so cargo
should have rebuilt. Checked rather than assumed:

    sh tools/probes/converter_rebuild_check/check.sh <scratch> \
      ~/compartilhado/babelfont-rs-worktrees/2026-10-22 ~/compartilhado/babelfont-rs-worktrees/2026-10-23

Result (result-2026-10-24.txt): both binaries are byte-identical after `cargo clean -p babelfont`
and a rebuild -- 2026-10-22 (58eedc82, cited by the 27 repositories of google/fonts#11162) and
2026-10-23 (7e58ba51, the 16 of PR-QUEUE 0b). Gugi converted by the saved and the rebuilt
binaries gives the same .glyphs apart from ids and dates.
