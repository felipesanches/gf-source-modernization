# crater-targets-2026-11-20

Inputs and checks of the fontc_crater branch crater-targets-2026-11-20, after google/fonts#11429 (Codystar, Dongle, Englebert and Gowun Batang reference their googlefonts repositories).

- `generated.json`: google-fonts-sources 0.11.2 (d7db2d8) run against [google/fonts 869789e84](https://github.com/google/fonts/tree/869789e84): `google-fonts-sources <dir> -o generated.json`, with `<dir>/google/fonts` a detached worktree of a google/fonts clone whose `origin/HEAD` exists.
- `merge.txt`: `tools/crater_targets.py <main's targets.json at 7eee146> generated.json`: 1602 -> 1602 entries; 4 added (googlefonts/codystar, dongle, englebert, gowunbatang), 4 removed (librefonts/codystar, librefonts/englebert, yangheeryu/Dongle, yangheeryu/Gowun-Batang), no other change.
- The four removed configs are also dropped from `results/skipped.json` (they were skipped because their google/fonts override configs listed .vfb files or a .zip archive); left there, crater's report lists them as "skipped configs are not in the inputs".
- `crater_local.txt`, `crater-local-results.json`: `RUSTUP_TOOLCHAIN=1.97.1 sh tools/crater_local.sh <old targets.json> <new targets.json> <scratch>` on the 4 new entries, with the branch's skipped.json in the output dir. fontc 9b9c966c (the rev of crater's 2026-11-19 run), rustc 1.97.1; Python pins in `python-pins.txt`.

Result: 16 targets (8 sources x default and gftools modes), 16 identical, 0 differ, 0 failed.
