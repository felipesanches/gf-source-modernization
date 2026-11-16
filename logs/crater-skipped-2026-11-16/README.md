# crater-skipped-2026-11-16

fontc_crater's `results/skipped.json` lists 9 google/fonts override configs that name FontLab `.vfb` files or a `.zip` archive (Lancelot, Bonbon, Federo, Iceland, Codystar, Englebert, Iceberg, Dongle, Gowun Batang). The 7 VFB families were in no batch table: `scope/census.py` takes families that gfonts_agents marks `missing_config` or `no_source`, and these had a config.

- `probe.txt`: `tools/probes/binary_to_source/probe.py <scratch> <shipped .ttf>...` on the 8 fonts those 7 families ship, taken from [google/fonts 2086013c](https://github.com/google/fonts/tree/2086013c4c53940b7214adc1f96764fa955b56ae). babelfont 26fdcfa9 (felipesanches/babelfont-rs branch 2026-11-02), gftools-builder 1e638bd (fontc 1.0.0).
- `landed-measurement.tsv`: `FAMILIES=families-binary.tsv OUT=<scratch> LANDED=<scratch>/landed.tsv tools/land.py <repo>` for the six `-TTF.vfb` imports, added to `families-binary.tsv` in this commit (P13: a `-TTF.vfb` import converts from the binary). The rows were uncommitted during the run, hence `-UNCOMMITTED-EVIDENCE`.

| family    | styles | result                                                         |
|-----------|--------|----------------------------------------------------------------|
| Codystar  | 2      | CLEAN                                                          |
| Bonbon    | 1      | hinting only                                                   |
| Lancelot  | 1      | hinting only (binary route; see below)                         |
| Federo    | 1      | hinting; advance of `nonmarkingreturn` (532 shipped, 0 built)  |
| Iceberg   | 1      | hinting; PCLT table                                            |
| Iceland   | 1      | hinting; PCLT table                                            |
| Englebert | 1      | GSUB `frac` and `ordn` lookups; head.version (1.655 shipped)   |

"hinting": the release carries TrueType instructions (prep, fpgm, cvt, glyph programs) that the build does not; everything else the functional gate checks passes (cmap, shaping, rendering, names, line spacing, advances, GDEF).

## Lancelot: VFB route against binary route

Lancelot's only `.vfb` (`Lancelot_source/Lancelot_Rom_Reg.vfb` at antonxheight/Lancelot 3039d277) is not a `-TTF` import, so both routes were measured. `lancelot-vfb-route.log`: `FAMILIES=<a one-row table of kind upstream> tools/land.py lancelot --unpublished-converter` with the VFB reader of babelfont-rs worktree vfb-integration (unpublished).

| route  | blocking rows | functional gate                                                     |
|--------|---------------|---------------------------------------------------------------------|
| binary | 0             | fails hinting only                                                  |
| VFB    | 23            | fails shaping, rendering, names, line spacing, advances and hinting |

The `.vfb` is an earlier state of the design, not what shipped: 7 outlines draw different ink (b, T, B, F, E, ...), 11 advances differ, the names read `Lancelot_Rom_Reg`, the vertical metrics differ and the release's `titl` feature is absent. Lancelot therefore joins `families-binary.tsv` with the six `-TTF.vfb` imports.

## Dongle and Gowun Batang: the Glyphs file inside the .zip

`sources/Dongle.zip` (yangheeryu/Dongle f7127c4d) and `sources/GowunBatang.zip` (yangheeryu/Gowun-Batang 4e73f5a9) each hold one Glyphs file of about 113 MB. Unzipped and built with `buildVariable: false` and crater's Python pins (gftools 0.10.8, fontmake 3.12.2, glyphsLib 6.17.1, ufo2ft 3.11.0, fonttools 4.68.0); scripts in research-scratch `sessions/2026-11-16_crater-skipped/`.

- Dongle does not build: `cannot map 'parallel' to U+2225; already mapped to 'dblverticalbar'`. The source gives `dblverticalbar` the code points 2016 and 2225 and `parallel` 2225; the shipped font maps U+2225 to `uni2016`.
- Gowun Batang builds. `gowunbatang-regular-gate.txt` and `gowunbatang-bold-gate.txt`: that build against the shipped fonts (`gate_source.py` with `BUILT=`). Same 12494 code points, names, line spacing and advance widths; 5 blocking rows each (GSUB script, feature and lookup lists, GDEF classes, vmtx). Shaping differs in 21554 of 11663056 runs (Regular) and 23547 of 11665116 (Bold); 130 and 3 top side bearings differ by 1 unit; one Regular outline (`uni2776`) draws different ink. The build is autohinted and the release is not (the default config; `autohintTTF: false` is what the release needs).

## Dongle and Gowun Batang: Glyphs route against binary route

| route                                             | Gowun Batang (Regular, Bold)                                                        | Dongle (Light, Regular, Bold)             |
|---------------------------------------------------|-------------------------------------------------------------------------------------|-------------------------------------------|
| binary (`probe-korean.txt`)                       | 1 blocking row each (GDEF glyph classes); functional gate passes                    | the same                                  |
| Glyphs, gftools-builder 1e638bd (pinned)          | 1261 rows (Regular); cmap, shaping, rendering, names, advances, GDEF fail           | 1095 and 1115 rows (Light, Regular)       |
| Glyphs, gftools-builder d93d65e (upstream main)   | 6 and 7 rows; shaping, rendering, names, advances (no vhea/vmtx), gasp fail         | build killed twice (exit 137), see below  |
| Glyphs, Python gftools 0.10.8                     | 5 rows each; shaping, advances (vmtx off by 1), hinting (config default) fail       | does not build without the source edit    |

- gftools-builder 1e638bd reads an all-digit Glyphs 2 code point (`unicode = 2002;`) as decimal: 332 code points land on other values (U+2002 becomes U+07D2). glyphslib 0.2.8 at that revision; upstream main d93d65e has glyphslib 0.4.1, which reads them as hexadecimal, and the build has the release's 12494 code points.
- The shaping difference is the same in the Python build and the d93d65e build (21554 of 11663056 runs for Regular, 23547 of 11665116 for Bold), so it does not come from the compiler. Against the release (`gsub_diff.py`, research-scratch): GSUB `ccmp` has 3 lookups in the release and 2 in the build; GPOS `mark` 2 and 9; 98 GDEF classes differ. The release was compiled by the repository's `build.py` from this file in June 2021.
- With d93d65e the Glyphs route also differs in `perthousand`'s outline, name IDs 4 and 6 of the Regular (`Gowun Batang`), usWeightClass of the Bold (400), and has no vhea/vmtx and no gasp.
- The binary-route sources are 30 to 55 MB per style; the upstream Glyphs files are about 113 MB.
- Dongle's source edit (`dongle_edit.py`, research-scratch): `parallel` loses `unicode = 2225`; the release maps U+2225 to `dblverticalbar` only and keeps `parallel` unencoded.

- Dongle's Glyphs file on gftools-builder d93d65e: the build was killed (exit 137) twice, the second time with nothing else running on a 32 GB machine; the builder had reached 9.5 GB after 40 seconds in the first attempt. The kernel log could not be read to confirm it was memory.
- Decision: both families convert from their binaries. Dongle's rows return to this track (its landing of October was CLEAN; it had been withdrawn when the zipped source was found).
