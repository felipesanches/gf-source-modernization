# production_names -- noProductionNames renamed to productionNames, and the 42 moved to it

**Model**: Claude Opus 5.5. **Date**: 2026-10-07.

Question: after renaming the builder key (cmyr on googlefonts/gftools#1229) to `productionNames`
(default true) in both builders, do the 42 repositories of google/fonts#11077 still build the
shipped fonts once their configs say `productionNames: false`?

The two renames, as patches against public bases:
- `gftools-productionNames.patch` -- googlefonts/gftools main 678696c4 (schema, recipe provider,
  docs, a test); tests/test_builder.py 13 passed; on Quantico-Regular `productionNames: false`
  keeps all 268 source names, the default renames 7.
- `gftools-rust-productionNames.patch` -- simoncozens/gftools-rust main bcd5230 (fontc
  operation, example config, a unit test); cargo test -p gftools-builder 14 passed.

Dry run (2026-10-07): `tools/rekey.py` on copies of the 42 repositories, built with gftools-rust
bcd5230 + the patch: 42 of 42 CLEAN -- every one of the 54 styles at 0 blocking table-gate rows,
the release's exact codepoints, functional gate PASS. verify_landed.py on one (Creepster Caps)
VERIFIED, and a planted builder-config commit that also touched README.md failed its SHAPE check.
The real run waits for the gftools-rust change to merge: land.B3_ID and the CI pin must name a
published revision.
