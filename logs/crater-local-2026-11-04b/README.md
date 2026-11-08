crater-local-2026-11-04b: do the 82 families of google/fonts #11234-#11237 build in fontc_crater, in both modes, before their targets PR? (tools/crater_local.sh; cmyr asked for this on #100.)

Targets: the targets.json of googlefonts/fontc_crater#117 (https://github.com/felipesanches/fontc_crater/commit/76288e8) plus the 82 entries of logs/crater-targets-2026-11-04b. fontc: googlefonts/fontc main 2f866adc (RUSTUP_TOOLCHAIN=1.97.1), fontc_crater built from it; venv from its resources/scripts/requirements.txt (gftools 0.10.6, fontmake 3.12.2, glyphsLib 6.17.1) plus its ttx_diff package: the same build as logs/crater-local-2026-11-04.

Run in four parts because of disk space (each crater run clones google/fonts, about 6 GB): `<part>.subset.json` lists the entries of each part, `<part>.summary.txt` its result, one line per target. Together they cover the 82 entries once each.

  RUSTUP_TOOLCHAIN=1.97.1 sh tools/crater_local.sh <targets of #117> <those plus a part's entries> <scratch>

| part       | entries | targets | built | same | differ | failed |
|------------|---------|---------|-------|------|--------|--------|
| chunk-00   | 10      | 26      | 26    | 26   | 0      | 0      |
| chunk-b00  | 4       | 8       | 8     | 8    | 0      | 0      |
| chunk-b01  | 4       | 8       | 8     | 8    | 0      | 0      |
| chunk-rest | 64      | 184     | 184   | 172  | 12     | 0      |
| total      | 82      | 226     | 226   | 214  | 12     | 0      |

"same": fontc's and fontmake's fonts are identical; "differ": both built and ttx_diff found differences. The 12 are 6 sources in both modes, all in `sizeof(GPOS)` (the size of the two GPOS tables differs): Niconne, Salsa and the four Share styles. The summaries were first written with a crater_local.sh that printed only built or failed; they were regenerated from the same results files with tools/crater_summary.py.

226 targets = 113 sources x (default, gftools).

After googlefonts/fontc_crater#118 merged, its CI run (https://github.com/googlefonts/fontc_crater/commit/8ccbcff, results/2026-11-06-154211.json, fontc d73bdfae) built the same 226 targets with the same result per target: 214 identical, 12 differ, 0 failed; none of the 4,163 existing targets changed category from the previous run (results/2026-11-05-163454.json). Checked with

  python3 tools/crater_ci_compare.py <8ccbcff:results/2026-11-06-154211.json> <8ccbcff^:results/2026-11-05-163454.json> logs/crater-local-2026-11-04b/chunk-*.summary.txt
