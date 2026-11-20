# crater-targets-2026-11-23

Inputs and the local crater check for the fontc_crater targets PR after google/fonts#11433 (36 VFB imports), #11434 (Beth Ellen and five googlefontdirectory-hg forks) and #11437 (Averia Libre, Averia Sans Libre, Averia Serif Libre, Sansation). Measured 2026-11-20. Branch crater-targets-2026-11-20b (Felipe, 2026-11-20: one PR replacing fontc_crater#130, keeping its two commits): #130's head cf6e5cb plus one commit with these 46; its targets.json equals `crater_targets.py <main's targets.json at 7eee146> generated.json` (50 added, 4 removed). Together with logs/crater-targets-2026-11-20 (#130's 16 targets) the local check covers all 50 new entries: 150 targets, all identical.

- `generated.json`: google-fonts-sources 0.11.2 (d7db2d8) against [google/fonts 06bfe0d62](https://github.com/google/fonts/tree/06bfe0d62) (`google-fonts-sources <dir> -o generated.json`, `<dir>/google/fonts` a detached worktree whose `origin/HEAD` exists).
- `merge.txt`: `tools/crater_targets.py <targets.json of fontc_crater#130's head cf6e5cb> generated.json`: 1602 -> 1648 entries, 46 added, none removed or re-pinned. Measured against #130's head so that its four families are not counted again.
- `crater_local.txt`, `crater-local-results.json`: `sh tools/crater_local.sh <old> <new> <scratch>` on the 46 new entries (rustc 1.97.1, fontc 9b9c966c, the rev of crater's 2026-11-19 run; Python pins in `python-pins.txt`), with #130's skipped.json in the output dir.

Result: 134 targets (the 46 entries' sources in default and gftools modes), 134 identical, 0 differ, 0 failed.
