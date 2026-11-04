crater-local-2026-11-04b: do the 82 families of google/fonts #11234-#11237 build in fontc_crater, in both modes, before their targets PR? (tools/crater_local.sh; cmyr asked for this on #100.)

Targets: the targets.json of googlefonts/fontc_crater#117 (https://github.com/felipesanches/fontc_crater/commit/76288e8) plus the 82 entries of logs/crater-targets-2026-11-04b. fontc: googlefonts/fontc main 2f866adc (RUSTUP_TOOLCHAIN=1.97.1), fontc_crater built from it; venv from its resources/scripts/requirements.txt (gftools 0.10.6, fontmake 3.12.2, glyphsLib 6.17.1) plus its ttx_diff package: the same build as logs/crater-local-2026-11-04.

Run in four parts because of disk space (each crater run clones google/fonts, about 6 GB): `<part>.subset.json` lists the entries of each part, `<part>.summary.txt` its result, one line per target. Together they cover the 82 entries once each.

  RUSTUP_TOOLCHAIN=1.97.1 sh tools/crater_local.sh <targets of #117> <those plus a part's entries> <scratch>

| part       | entries | targets | succeeded | failed |
|------------|---------|---------|-----------|--------|
| chunk-00   | 10      | 26      | 26        | 0      |
| chunk-b00  | 4       | 8       | 8         | 0      |
| chunk-b01  | 4       | 8       | 8         | 0      |
| chunk-rest | 64      | 184     | 184       | 0      |
| total      | 82      | 226     | 226       | 0      |

226 targets = 113 sources x (default, gftools).
