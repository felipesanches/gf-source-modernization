# crater-targets-2026-11-13

Inputs and summary of the second commit on the fontc_crater targets branch crater-targets-2026-11-12 (googlefonts/fontc_crater#122), after google/fonts#11312, #11313, #11314 (corrected pins) and #11317 (`buildVariable: false` in 14 more overrides).

- `generated.json`: google-fonts-sources 0.11.2 run against [google/fonts 3e566776](https://github.com/google/fonts/tree/3e5667764ccfea32ce0c3d58a3a4756de890adc1): `google-fonts-sources <dir> -o generated.json`, with `<dir>/google/fonts` a detached worktree at that commit. `generate.log` is the tool's output.
- `merge.txt`: what `tools/crater_targets.py <branch targets.json> generated.json` reported: 1573 -> 1574 entries; 8 added, 7 removed, 14 re-pinned.
- `crater-local-tally.txt`: `fontc_crater ci` on the 36 changed entries (`tools/crater_local.sh`; the 22 added or re-pinned ones, plus the 14 overrides of #11317, removed from the old file so they count as new), tallied by `tools/probes/crater_local/crater_local_tally.py`. fontc 5715ced0 (rustc 1.97.1), gftools 0.10.8, fontmake 3.12.2, glyphsLib 6.17.1, ufo2ft 3.11.0, fonttools 4.68.0.

Result for the 36 entries, 171 targets:

| mode    | result              | targets |
|---------|---------------------|---------|
| gftools | identical           | 55      |
| gftools | differ              | 2       |
| gftools | fontc fails only    | 50      |
| gftools | fontmake fails only | 9       |
| gftools | both fail           | 11      |
| default | identical           | 18      |
| default | differ              | 9       |
| default | fontc fails only    | 2       |
| default | fontmake fails only | 2       |
| default | both fail           | 13      |

- fontc fails only (gftools mode), 50: 46 are static instances at no master's location, which fontc does not interpolate (40 in the 14 overrides of #11317, as counted from the sources beforehand; 2 each in Amita, Unna and Playfair Display SC). The other 4: Harmattan Regular and Bold (GPOS table packing overflows), Bahianita (glyph 'manat': 2 consecutive offcurve points), Playpen Sans (FEA parsing).
- Identical for the first time or again: Charis SIL (4 statics), Jaldi, Pacifico, Plus Jakarta Sans, Ruda, Sahitya, Srisakdi, Sura, Courier Prime, Rowdies, Charmonman.
- Both fail: Hepta Slab (incompatible glyph uniEFFD), Kumar One and Outline ("No final targets"), Rakkas ('_top_2' anchor), Rhodium Libre (duplicate bracket glyph), Vesper Libre, Playfair Display (gftools names the fonts `[wdth,wght]`, which the config's stat block does not list), two Playfair Display SC instances.

`crater-local-union.txt`: this run and the 2026-11-12 one (the 21 overrides of #11277 and #11303) taken together, by `tools/probes/crater_local/crater_local_union.py <2026-11-12 results> <2026-11-13 results>`: 54 entries (Srisakdi, Kumar One and Kumar One Outline are in both; the later results count), 320 targets. Both runs used fontc 5715ced0 and the same Python pins.

## Third commit: google/fonts#11323 (Khula, Nerko One)

`khula-nerkoone/`: regenerated against [google/fonts b78877b7](https://github.com/google/fonts/tree/b78877b777ed3a18a1b431b0df7d8ee3f84c2e5f): no entry changes (`merge.txt`), only `fonts_repo_sha`. Local crater on the two entries, 12 targets (`crater-local-tally.txt`): Nerko One identical in both modes; Khula's five UFOs build with fontmake and fail in fontc in both modes. fontc's error: `feature pres {` opens in `UFO/Khula-shaping.fea` and closes in the next included file, `UFO/<Weight>/feat/<Weight>-Ivowel.fea` ("Feature block is unclosed"). `crater-local-union.txt` now covers the three runs: 56 entries, 332 targets.
