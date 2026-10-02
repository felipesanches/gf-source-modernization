# play probes

| script | question | command |
|---|---|---|
| `build_upstream.sh` | Does alexeiva/play v2.101 (d84ad58) build with gftools-builder3 e851b8b / fontc 1.0.0, and how close is it to the shipped Play? Three runs: as is; without ringcomb.case's anchors (probe only); statics only. | `sh build_upstream.sh [workdir]` -> `../runs/build_upstream.txt` |
| `cmap_hex_as_decimal.py` | Of the codepoints a build lost, how many sit at their hex digits read as decimal (U+2013 -> U+07DD)? | `$PY cmap_hex_as_decimal.py <shipped> <built>` -> `../runs/cmap_hex_as_decimal-Play-Regular.txt` |
| `glyphs2_unicode/` | Minimal two-glyph Glyphs 2 repro of both glyphslib-rs bugs (see its README). | `sh glyphs2_unicode/run.sh` |
| `glyphs_route_residuals.py` | For the Glyphs-source landing (../README-glyphs-route.md): languagesystems, zero-width mark offsets, weight class, panose, underline, names, GDEF mark classes, production names and point counts, release vs build. | `$PY glyphs_route_residuals.py <shipped> <built>` -> `../runs/glyphs_route_residuals.txt` |

fontc stops at whichever failure its parallel jobs reach first, so the list of
interpolation-incompatible glyphs varies per run: `../runs/build_upstream.txt` lists 3,
`../runs/build_upstream-variable-earlier-run.log` (same config, earlier run) 53.
The statics-only run writes one font, Regular or Bold, whichever finished last.
