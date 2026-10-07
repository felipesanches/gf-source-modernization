# crater_gftools_pin -- what moving fontc_crater's gftools pin changes

**Model**: Claude Opus 5.5. **Date**: 2026-10-07.

Question: crater pins gftools 0.9.93 (googlefonts/fontc resources/scripts/requirements.txt) "to
ensure ttx-diff output is stable". Our 42 targets (googlefonts/fontc_crater#100) need a newer
gftools in gftools mode. What would a newer pin change for EXISTING targets?

Method: crater itself (fontc 04ff1194, fontmake 3.12.1, fonttools 4.66.1, glyphsLib 6.15.0,
ufo2ft 3.9.1 in every run), on `sample-entries.txt` -- the 4 entries crater's 2026-10-05 run
failed with `--keep-direction`, plus 40 random entries of targets.json (seed 20261007) --
and on our 42 new entries; per target, `compare.py` reports status changes and, for targets
that build in both runs, whether ttx_diff's fontc-vs-fontmake scores moved.

| comparison | result |
|---|---|
| 0.9.93 -> 0.10.0, sample (108 targets) | 87 unchanged ok (scores identical), 14 unchanged failures; Workbench fixed; **Katibeh regresses** (`KeyError: 'customParameters'`); 5 fail differently |
| 0.9.93 -> main b42647c3 + both gftools changes, sample | 88 unchanged ok (scores identical), 13 unchanged failures; Workbench fixed; Katibeh ok; 6 fail differently, no target newly failing |
| 0.9.93 -> main + both changes, our 42 (108 targets) | 54 default unchanged ok; 54 gftools-mode FAIL -> ok |

The two gftools changes: accept `noProductionNames` (../gftools_no_production_names), and treat a
.glyphs file without font-level customParameters as static (the 0.10.0 Katibeh regression).
"Fail differently" rows are pre-existing failures with a new message: Balsamiq Sans and
Sixtyfour lose `--keep-direction` and now show their own source errors (bad anchors; "Locations
must be unique"); LXGW Marker Gothic fails in one compiler instead of two; one Balsamiq Sans
default-mode row only names a different bad glyph first (default mode does not use gftools).

Conclusion: move the pin straight to a gftools release containing both changes, not to 0.10.0.
Crater reuses cached results when only Python tools change: every run here cleared
<cache>/crater_cached_results first.

Both gftools changes merged upstream 2026-10-07: googlefonts/gftools#1229 (678696c4) and #1230
(d8a6e227); main at 678696c4 has the same library code as the tree measured here.
