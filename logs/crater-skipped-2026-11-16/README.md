# crater-skipped-2026-11-16

fontc_crater's `results/skipped.json` lists 9 google/fonts override configs that name FontLab `.vfb` files or a `.zip` archive (Lancelot, Bonbon, Federo, Iceland, Codystar, Englebert, Iceberg, Dongle, Gowun Batang). The 7 VFB families were in no batch table: `scope/census.py` takes families that gfonts_agents marks `missing_config` or `no_source`, and these had a config.

- `probe.txt`: `tools/probes/binary_to_source/probe.py <scratch> <shipped .ttf>...` on the 8 fonts those 7 families ship, taken from [google/fonts 2086013c](https://github.com/google/fonts/tree/2086013c4c53940b7214adc1f96764fa955b56ae). babelfont 26fdcfa9 (felipesanches/babelfont-rs branch 2026-11-02), gftools-builder 1e638bd (fontc 1.0.0).
- `landed-measurement.tsv`: `FAMILIES=families-binary.tsv OUT=<scratch> LANDED=<scratch>/landed.tsv tools/land.py <repo>` for the six `-TTF.vfb` imports, added to `families-binary.tsv` in this commit (P13: a `-TTF.vfb` import converts from the binary). The rows were uncommitted during the run, hence `-UNCOMMITTED-EVIDENCE`.

| family    | styles | result                                                         |
|-----------|--------|----------------------------------------------------------------|
| Codystar  | 2      | CLEAN                                                          |
| Bonbon    | 1      | hinting only                                                   |
| Lancelot  | 1      | hinting only (probe; its `.vfb` is not a `-TTF` import)        |
| Federo    | 1      | hinting; advance of `nonmarkingreturn` (532 shipped, 0 built)  |
| Iceberg   | 1      | hinting; PCLT table                                            |
| Iceland   | 1      | hinting; PCLT table                                            |
| Englebert | 1      | GSUB `frac` and `ordn` lookups; head.version (1.655 shipped)   |

"hinting": the release carries TrueType instructions (prep, fpgm, cvt, glyph programs) that the build does not; everything else the functional gate checks passes (cmap, shaping, rendering, names, line spacing, advances, GDEF).
