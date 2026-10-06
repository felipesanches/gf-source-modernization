# crater_local -- the 42 new targets of googlefonts/fontc_crater#100, run in crater itself

**Model**: Claude Opus 5.5. **Date**: 2026-10-06.

Question (cmyr on fontc_crater#100): do the targets the PR adds build in crater, in both of
its modes, and if not, what fixes them? Run with `tools/crater_local.sh` on the 42 entries new
in the PR's targets.json (54 sources), fontc_crater from googlefonts/fontc 04ff1194 (main,
2026-10-05), three Python environments differing only in gftools:

| run | gftools | default mode | gftools mode |
|---|---|---|---|
| 1 | 0.9.93 (crater's pin) | 54 ok | 0 ok: 54 "ValueError: Invalid configuration file" |
| 2 | 0.9.93 + noProductionNames.patch | 54 ok | 33 ok; 21 "unknown fontmake arg '--keep-direction'" |
| 3 | main 600993df + noProductionNames.patch | 54 ok | 54 ok |

- Run 1: Python gftools' schema rejects `noProductionNames` (gftools-rust's key) in our configs.
- Run 2: the patch (../gftools_no_production_names/noProductionNames.patch) removes that; the 21
  left set `reverseOutlineDirection: false`, which gftools 0.9.93's fontc path refuses. That is
  not ours: the official crater run of 2026-10-05 shows it for Balsamiq Sans, Sixtyfour and
  Workbench too. gftools fixed it in f8b5753c (#1219, 2026-08-28; in v0.10.0).
- Run 3: with both, every target builds in both modes.

So crater's gftools-mode targets for these repositories need a gftools release with the
patch, and crater's gftools pin (fontc resources/scripts/requirements.txt) moved to it.

Files: results-1-crater-pins.txt, results-2-gftools-0.9.93-plus-patch.txt,
results-3-gftools-main-plus-patch.txt (one line per target; for failures, the last stderr line).
Run 2 and 3 were run with crater's result cache cleared: crater reuses cached results when
only the Python tools change.
