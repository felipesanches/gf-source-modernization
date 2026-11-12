# Reader fixes for jsMath and Datatype (2026-11-12)

Question: the re-probe (`../README.md`) failed jsMath x6 on the space advance and could not build
Datatype. Where does each failure come from, and what do the fixes leave?

| finding                                                                      | where it is                                                                                                                                                                                                           | fix (branch, unpublished when this was written)                  |
|------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------|
| jsMath: `space` advance 65534 read as -2 (built 0)                           | skrifa `FixedScaleFactor::apply` truncates its product to a 16.16 Fixed, so `Size::unscaled()` wraps at 32768 units                                                                                                   | fontations `skrifa-unscaled-metrics`: multiply-divide in 64 bits |
| Datatype: static build fails, "No master was present at location"            | the probe config (`buildVariable: false`): gftools-builder then makes each static with InstantiateSource, which needs a master at the instance; not `active = 0` and not the rounding (`datatype_static_variants.sh`) | `probe.py` VARIABLE=1 builds the variable font                   |
| Datatype: variable build fails in fontc, wght mapping user 400 -> design 900 | babelfont's Glyphs writer omits an unmapped axis from Axis Mappings; read back, the instances (no weight class) all map to user 400                                                                                   | babelfont-rs `glyphs3-unmapped-axes`                             |
| Datatype: instances at wght 199.9939, 700.0183, ...                          | babelfont's TTF reader reads fvar instances through F2Dot14                                                                                                                                                           | babelfont-rs `ttf-instance-user-coords`                          |

Inputs: babelfont-rs main `f1458803` with both babelfont branches merged, built against skrifa
0.46.2 (the version babelfont locks) with `skrifa-0.46.2-scaled64.patch` (the skrifa branch's
change) through `[patch.crates-io]`; gftools-builder `tools/land.py` B3_DEFAULT; google/fonts
`c30b221be`.

Rerun:

    BF=<babelfont as above> B3=<gftools-builder> PY=<python> \
      sh tools/probes/binary_to_source/probe_batch.sh <google/fonts> reader-fixes/jsmath-worklist.txt <scratch>
    VARIABLE=1 BF=<babelfont as above> B3=<gftools-builder> \
      python3 tools/probes/binary_to_source/probe.py <scratch> '<google/fonts>/ofl/datatype/Datatype[wdth,wght].ttf'

Result (`jsmath-summary.tsv`, `logs/`; the `'space'=2` is fontTools' huge-advance warning):

| family                                       | before                               | after                                                                                                                                                                                                                                                                                |
|----------------------------------------------|--------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| jsMath cmex10, cmmi10, cmr10, cmsy10, cmti10 | shaping, advances, hinting; hmtx row | hinting only, 0 rows                                                                                                                                                                                                                                                                 |
| jsMath cmbx10                                | the same + line_spacing              | hinting + line_spacing (fsSelection BOLD, macStyle bold), 0 rows                                                                                                                                                                                                                     |
| Datatype (variable)                          | build failed                         | builds; cmap, shaping, rendering, line_spacing, advances, gdef, hinting PASS; names FAIL (the default master is named "Default", so ID 1/4/17 read "Datatype Default"); 9 rows: STAT (the build adds an axis ARRR), fvar instance PostScript name IDs, gvar shared tuple order, meta |
