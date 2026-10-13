# binary_to_source: results (2026-10-08)

Question: can a family Google Fonts ships with no sources anywhere be given a source by
converting its own binary with babelfont, and does that source rebuild the binary?

Answer: yes, once babelfont's TTF reader reads a static font as it renders and shapes. With
upstream babelfont the conversions differed in names, OS/2 values, kerning and outlines; with
the reader fixes below, two families come back CLEAN and four more behave identically, their
only table difference being a legacy `kern` table that is now a GPOS kern feature.

## Inputs

- Shipped fonts: google/fonts 2eb0b48d5f760f62e286216f0859a8c540dbc1bd (every .ttf measured
  here is byte-identical there and in the clone the runs read).
- Builder: gftools-builder from simoncozens/gftools-rust#1 at 5a2567604b8f (productionNames),
  fontc 1.0.0.
- Gates: tools/table_gate.py and tools/functional_gate.py at this commit; diffenator3 1.1.4.
- Converter, "before": simoncozens/babelfont-rs main 3dabb000 (upstream, unmodified).
- Converter, "after": 3dabb000 plus `babelfont/sr-aef-uncompile-fixes/` (3 patches),
  `babelfont/ttf-static-font-fidelity/` (16 patches) and the typographic-family-names branch
  (pr-bodies/babelfont-typographic-family-names.md), as one tree:
  `babelfont/measure-integration.diff`; `babelfont/rebuild.sh <dir>` rebuilds that exact tree
  from public upstream (it checks the SHA-256 of the file listing) and builds it.

Rerun: `BF=<babelfont> B3=<gftools-builder> python3 probe.py <scratch> <shipped.ttf>...`
(README.md); logs in `results/`.

2026-10-13: the babelfont branches were rebased onto upstream d44f2bdc (4 + 20 patches; the
integration diff and rebuild.sh now apply to d44f2bdc). Upstream had added native vertical
metrics, so the reader now states vhea as the master's vhea metrics and vmtx as each layer's
vertical advance and origin (the Glyphs writer drops a vertWidth equal to the typo ascender
minus descender, as glyphsLib does). All 12 landed families were re-landed with that converter
(`land.py <repo> --rebuild --unpublished-converter`, the measured babelfont): every verdict is
unchanged -- 8 CLEAN, and Averia x3 and Sansation RESIDUAL as before; Dongle CLEAN 3/3 with 12550
vertOrigin values and no vertWidth (every advance is the default).

## The sample (results/final-sample.log, results/before-sample.log)

| family | styles | before (upstream 3dabb000) | after |
|---|---|---|---|
| Della Respira | 1 | functional FAIL 1/1 (line_spacing, names, rendering); 2 table rows | CLEAN |
| Oranienbaum | 1 | functional FAIL 1/1 (advances, gdef, names); 3 table rows | CLEAN |
| Averia Libre | 6 | functional FAIL 6/6 (advances, line_spacing, names, rendering, shaping); 3 table rows | functional PASS 6/6; 3 table rows: legacy kern -> GPOS |
| Averia Sans Libre | 6 | functional FAIL 6/6 (advances, line_spacing, names, rendering, shaping); 3 table rows | functional PASS 6/6; 3 table rows: legacy kern -> GPOS |
| Averia Serif Libre | 6 | functional FAIL 6/6 (advances, line_spacing, names, rendering, shaping); 4-5 table rows | functional PASS 6/6; 3 table rows: legacy kern -> GPOS |
| Sansation | 6 | functional FAIL 5/6 (advances, gdef, line_spacing, names, rendering, shaping); 6 table rows; 1 style(s) do not build | functional PASS 5/6; Light Italic loses fsSelection ITALIC (fontc) |

Della Respira turned out not to be binary-only: its FontForge source is in Nathan Willis's
Bazaar branch on Launchpad (lp:revivalism-fonts, `dellarespira/src/dellarespira-regular.sfd`,
history from 2011), which the library census, reading git repositories only, could not see.
It belongs with the .sfd conversions (the shipped font says version 0.201, FontForge
2012-03-28; the trunk's .sfd says 0.2 and was edited again in 2013), and is no longer in
families-binary.tsv. Its row above stays as a measurement of the reader.

Legacy kern -> GPOS: the table gate's legacy-kern arbitration (all kerned pairs must shape
alike) fails for the Averia families only on soft-hyphen pairs, which HarfBuzz hides; the
difference is half the pair's value on the next glyph (`legacy_kern_pairs.py`,
results/legacy-kern-pairs.txt). Sansation's release has a GPOS without a kern feature, so the
arbitration does not apply, but all 1097 pairs shape alike. Sansation's other rows: the GSUB
script's feature indices in another (by the spec arbitrary) order, and in Light Italic two
rows from the release naming two glyphs `ffi` (the table gate reads glyphs by name; the
functional gate pairs them by correspondence and finds them equal).

## Other families tried (results/final-others.log)

| family | after | why |
|---|---|---|
| GFS Didot | functional FAIL (shaping) | its GPOS registers `grek` with no features, so Greek text is not kerned; no FEA compiler keeps an empty script registration, and without it HarfBuzz falls back to `latn`'s kerning |
| Averia Gruesa Libre | functional FAIL (names, fsSelection) | an upright font with italic angle -1.7; fontc flags any nonzero angle italic, and names the style Italic |
| IM Fell English SC | functional FAIL (shaping, GDEF) | 246 runs with a combining comma below (U+0326) shape differently. Measured: fontc's kern lookup does not skip that mark (it has an advance, so fontc puts it in a mark filtering set) where HarfBuzz applies the release's legacy kern skipping marks. Not measured, suspected too: the release has no GPOS, so HarfBuzz positions marks itself, which any GPOS turns off. Also head.font_direction_hint 0 (decision D6 in investigations/next-provenance/FINDINGS.md, open) |
| Siemreap, Phetsarath | functional FAIL (shaping) | not investigated: Khmer and Lao runs shape differently (Siemreap 80272 of 164513 runs, Phetsarath Regular 2535 of 29332). Both releases have a GPOS that registers scripts with no features (as GFS Didot's) and AAT tables (feat, morx); Phetsarath Bold also VTT sources (TSI*) |
| Yinmar | build fails | 12 "undefined mark class" errors: GPOS mark lookups still name mark classes (`@bottomleft`) that the reader turned into anchors and does not define |
| Zen Antique | build fails | anchors named `_mark_class_0_2`, which fontc refuses ("mark anchors cannot be numbered") |

## What the reader fixes changed

See the commit messages of the two patch series and pr-bodies/babelfont-ttf-static-font-fidelity.md
and pr-bodies/sr-aef-uncompile-fixes.md.

## Later families (2026-10-09)

One family at a time, each probed, then landed with tools/land.py (families-binary.tsv). The
converter follows `babelfont/measure-integration.diff` (`babelfont/refresh.sh` regenerates it
and the patch series after each change); landed families are re-landed on the latest one.

| family | styles | result |
|---|---|---|
| Reenie Beanie | 1 | CLEAN (hand hinting in VTT replaced by ttfautohint; disclosed) |
| PT Serif | 4 | CLEAN once a font without GDEF glyph classes is given none (before: 13995 of 2250538 runs differed, accents that ccmp substitutes keeping their advance); hinting disclosed |
| PT Sans Narrow | 2 | CLEAN once usWidthClass (3) travels as FEA, as usWeightClass does (fontc 1.0.0 drops a single master's instance widthClass too); hinting disclosed |
| PT Sans Caption | 2 | CLEAN; hinting disclosed |
| Almarai | 4 | CLEAN once the reader defines the mark classes its uncompiled mark lookups name, and sr-aef stops naming a made-up mark anchor `_mark_class_<c>_<n>` (fontc: "mark anchors cannot be numbered"); hinting disclosed |
| IM Fell English SC | 1 | not landed: 246 of 932722 runs differ, all with U+0326. The release has a legacy kern table and no GPOS, so HarfBuzz positions the comma below itself (fallback); the build kerns through GPOS, which turns the fallback off (`0` + U+0326: release offset 501,-58, build 1004,0). Plus head.font_direction_hint 0. Felipe's decision |
| Anonymous Pro | 4 | not landed: the release embeds bitmap strikes (EBDT, EBLC, EBSC), which a .glyphs source cannot carry; the reader also loses post.isFixedPitch |
| Khmer | 1 | not landed: Khmer substitutions differ (6930 of 36123 runs; U+17B6 alone becomes uni1794.a2 in the release and stays uni17B6 in the build); shaped through AAT, see below |
| Yinmar | 1 | not landed, for the same reason as Khmer (19621 of 80657 runs differ) |

Khmer, Yinmar, Siemreap and Phetsarath carry an AAT `morx` table beside GSUB, and HarfBuzz
shapes horizontal text with `morx` when a font has one: removing `morx` from a copy of the
Yinmar release makes it shape exactly as the build (U+102B gets a dotted circle, U+1026
decomposes to U+1025 U+102E). fontc writes no AAT tables, so under HarfBuzz these four
cannot be reproduced; under an engine that reads GSUB they were never shaped by `morx`.

| family | styles | result |
|---|---|---|
| Jua | 1 | CLEAN; hinting disclosed |
| Dongle | 3 | CLEAN once the reader reads vertical metrics (vhea; vmtx as Glyphs vertWidth/vertOrigin, since 2026-10-13 through babelfont's native vertical advance and origin) |
| Shippori Mincho | 5 | not landed: its Japanese name records (IDs 1, 2, 4, 6, 16; Windows 0x411) do not reach the build. The reader read the undecodable MacJapanese record as an empty "ja" name (fixed on the ttf branch); babelfont's Glyphs writer then writes BCP-47 language codes ("ja-JP"), which fontc does not know, and the branch that writes such names as Name Table Entry parameters (glyphs3-localized-name-entries) conflicts with typographic-family-names in export_name_table_entries: the two need reconciling first. Regular otherwise CLEAN (0 table rows) |
| Homemade Apple | 1 | CLEAN (2026-10-13). The release has no glyph instructions (its fpgm defines functions no glyph calls; its prep only turns on dropout control); the build is ttfautohinted, as for every release with an fpgm; disclosed |
| Calligraffitti | 1 | CLEAN (2026-10-13); hinting disclosed |
| Kranky | 1 | CLEAN (2026-10-13); legacy kern (629 pairs) as GPOS and unhinted glyphs disclosed |
| Cherry Cream Soda | 1 | CLEAN (2026-10-13); legacy kern (1125 pairs) as GPOS and hinting disclosed |

Not binary-only after all (2026-10-13): Schoolbell, Walter Turncoat, Slackey, Sunshiney,
Permanent Marker and Rock Salt are on the NO-SOURCES list, but their upstream_info.md records
.vfb/.sfd sources ("legacy formats only"). They belong to the SFD/VFB tracks, which convert a
source (after establishing which format the release was mastered from), not to this one.
