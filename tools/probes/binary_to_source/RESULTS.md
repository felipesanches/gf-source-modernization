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
Later the same day the measured converter also took simoncozens/babelfont-rs#117 (localized
names no Glyphs property holds, and languages Glyphs has no code for, as Name Table Entry)
plus a new commit on it (a Macintosh name record gets no Windows entry): the measured babelfont.
All 22 families landed by then were re-landed with it: every verdict unchanged, 18 CLEAN and
4 RESIDUAL (Averia x3, Sansation).

## The sample (results/final-sample.log, results/before-sample.log)

| family             | styles | before (upstream 3dabb000)                                                                                           | after                                                              |
|--------------------|--------|----------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------|
| Della Respira      | 1      | functional FAIL 1/1 (line_spacing, names, rendering); 2 table rows                                                   | CLEAN                                                              |
| Oranienbaum        | 1      | functional FAIL 1/1 (advances, gdef, names); 3 table rows                                                            | CLEAN                                                              |
| Averia Libre       | 6      | functional FAIL 6/6 (advances, line_spacing, names, rendering, shaping); 3 table rows                                | functional PASS 6/6; 3 table rows: legacy kern -> GPOS             |
| Averia Sans Libre  | 6      | functional FAIL 6/6 (advances, line_spacing, names, rendering, shaping); 3 table rows                                | functional PASS 6/6; 3 table rows: legacy kern -> GPOS             |
| Averia Serif Libre | 6      | functional FAIL 6/6 (advances, line_spacing, names, rendering, shaping); 4-5 table rows                              | functional PASS 6/6; 3 table rows: legacy kern -> GPOS             |
| Sansation          | 6      | functional FAIL 5/6 (advances, gdef, line_spacing, names, rendering, shaping); 6 table rows; 1 style(s) do not build | functional PASS 5/6; Light Italic loses fsSelection ITALIC (fontc) |

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

| family               | after                                | why                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
|----------------------|--------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| GFS Didot            | functional FAIL (shaping)            | its GPOS registers `grek` with no features, so Greek text is not kerned; no FEA compiler keeps an empty script registration, and without it HarfBuzz falls back to `latn`'s kerning                                                                                                                                                                                                                                                                                          |
| Averia Gruesa Libre  | functional FAIL (names, fsSelection) | an upright font with italic angle -1.7; fontc flags any nonzero angle italic, and names the style Italic                                                                                                                                                                                                                                                                                                                                                                     |
| IM Fell English SC   | functional FAIL (shaping, GDEF)      | 246 runs with a combining comma below (U+0326) shape differently. Measured: fontc's kern lookup does not skip that mark (it has an advance, so fontc puts it in a mark filtering set) where HarfBuzz applies the release's legacy kern skipping marks. Not measured, suspected too: the release has no GPOS, so HarfBuzz positions marks itself, which any GPOS turns off. Also head.font_direction_hint 0 (decision D6 in investigations/next-provenance/FINDINGS.md, open) |
| Siemreap, Phetsarath | functional FAIL (shaping)            | not investigated: Khmer and Lao runs shape differently (Siemreap 80272 of 164513 runs, Phetsarath Regular 2535 of 29332). Both releases have a GPOS that registers scripts with no features (as GFS Didot's) and AAT tables (feat, morx); Phetsarath Bold also VTT sources (TSI*)                                                                                                                                                                                            |
| Yinmar               | build fails                          | 12 "undefined mark class" errors: GPOS mark lookups still name mark classes (`@bottomleft`) that the reader turned into anchors and does not define                                                                                                                                                                                                                                                                                                                          |
| Zen Antique          | build fails                          | anchors named `_mark_class_0_2`, which fontc refuses ("mark anchors cannot be numbered")                                                                                                                                                                                                                                                                                                                                                                                     |

## What the reader fixes changed

See the commit messages of the two patch series and pr-bodies/babelfont-ttf-static-font-fidelity.md
and pr-bodies/sr-aef-uncompile-fixes.md.

## Later families (2026-10-09)

One family at a time, each probed, then landed with tools/land.py (families-binary.tsv). The
converter follows `babelfont/measure-integration.diff` (`babelfont/refresh.sh` regenerates it
and the patch series after each change); landed families are re-landed on the latest one.

| family             | styles | result                                                                                                                                                                                                                                                                                                                                |
|--------------------|--------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Reenie Beanie      | 1      | CLEAN (hand hinting in VTT replaced by ttfautohint; disclosed)                                                                                                                                                                                                                                                                        |
| PT Serif           | 4      | CLEAN once a font without GDEF glyph classes is given none (before: 13995 of 2250538 runs differed, accents that ccmp substitutes keeping their advance); hinting disclosed                                                                                                                                                           |
| PT Sans Narrow     | 2      | CLEAN once usWidthClass (3) travels as FEA, as usWeightClass does (fontc 1.0.0 drops a single master's instance widthClass too); hinting disclosed                                                                                                                                                                                    |
| PT Sans Caption    | 2      | CLEAN; hinting disclosed                                                                                                                                                                                                                                                                                                              |
| Almarai            | 4      | CLEAN once the reader defines the mark classes its uncompiled mark lookups name, and sr-aef stops naming a made-up mark anchor `_mark_class_<c>_<n>` (fontc: "mark anchors cannot be numbered"); hinting disclosed                                                                                                                    |
| IM Fell English SC | 1      | not landed: 246 of 932722 runs differ, all with U+0326. The release has a legacy kern table and no GPOS, so HarfBuzz positions the comma below itself (fallback); the build kerns through GPOS, which turns the fallback off (`0` + U+0326: release offset 501,-58, build 1004,0). Plus head.font_direction_hint 0. Felipe's decision |
| Anonymous Pro      | 4      | not landed: the release embeds bitmap strikes (EBDT, EBLC, EBSC), which a .glyphs source cannot carry; the reader also loses post.isFixedPitch                                                                                                                                                                                        |
| Khmer              | 1      | not landed: Khmer substitutions differ (6930 of 36123 runs; U+17B6 alone becomes uni1794.a2 in the release and stays uni17B6 in the build); shaped through AAT, see below                                                                                                                                                             |
| Yinmar             | 1      | not landed, for the same reason as Khmer (19621 of 80657 runs differ)                                                                                                                                                                                                                                                                 |

Khmer, Yinmar, Siemreap and Phetsarath carry an AAT `morx` table beside GSUB, and HarfBuzz
shapes horizontal text with `morx` when a font has one: removing `morx` from a copy of the
Yinmar release makes it shape exactly as the build (U+102B gets a dotted circle, U+1026
decomposes to U+1025 U+102E). fontc writes no AAT tables, so under HarfBuzz these four
cannot be reproduced; under an engine that reads GSUB they were never shaped by `morx`.

| family                                               | styles | result                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
|------------------------------------------------------|--------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Jua                                                  | 1      | CLEAN; hinting disclosed                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| Dongle                                               | 3      | CLEAN once the reader reads vertical metrics (vhea; vmtx as Glyphs vertWidth/vertOrigin, since 2026-10-13 through babelfont's native vertical advance and origin)                                                                                                                                                                                                                                                                                                                                                                                          |
| Shippori Mincho                                      | 5      | not landed: its Japanese name records (IDs 1, 2, 4, 6, 16; Windows 0x411) do not reach the build. The reader read the undecodable MacJapanese record as an empty "ja" name (fixed on the ttf branch); babelfont's Glyphs writer then writes BCP-47 language codes ("ja-JP"), which fontc does not know, and the branch that writes such names as Name Table Entry parameters (glyphs3-localized-name-entries) conflicts with typographic-family-names in export_name_table_entries: the two need reconciling first. Regular otherwise CLEAN (0 table rows) |
| Homemade Apple                                       | 1      | CLEAN (2026-10-13). The release has no glyph instructions (its fpgm defines functions no glyph calls; its prep only turns on dropout control); the build is ttfautohinted, as for every release with an fpgm; disclosed                                                                                                                                                                                                                                                                                                                                    |
| Calligraffitti                                       | 1      | CLEAN (2026-10-13); hinting disclosed                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| Kranky                                               | 1      | CLEAN (2026-10-13); legacy kern (629 pairs) as GPOS and unhinted glyphs disclosed                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| Cherry Cream Soda                                    | 1      | CLEAN (2026-10-13); legacy kern (1125 pairs) as GPOS and hinting disclosed                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| Chewy                                                | 1      | CLEAN (2026-10-13); legacy kern (399 pairs) as GPOS and hinting disclosed                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| Coming Soon                                          | 1      | CLEAN (2026-10-13); its GPOS kern kept and its legacy kern table (861 pairs, read only without GPOS) not carried; unhinted glyphs; disclosed                                                                                                                                                                                                                                                                                                                                                                                                               |
| Crafty Girls                                         | 1      | CLEAN (2026-10-13); legacy kern (375 pairs) as GPOS and hinting disclosed                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| Fontdiner Swanky                                     | 1      | CLEAN (2026-10-13); legacy kern (3290 pairs) as GPOS and unhinted glyphs disclosed                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| Akronim                                              | 1      | CLEAN (2026-10-13); legacy kern (1051 pairs) as GPOS and partial hinting disclosed                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| Porter Sans Block                                    | 1      | CLEAN (2026-10-13); its GPOS kern kept and its legacy kern table (2209 pairs) not carried; hinting disclosed                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| Gugi                                                 | 1      | CLEAN (2026-10-13) once its Korean names (Windows 0x0412) reach the build: the Glyphs writer gave them the BCP-47 code "ko-KR", which fontc does not read; #117 writes them as Name Table Entry, and its new commit keeps the Macintosh English records out of those; hinting disclosed                                                                                                                                                                                                                                                                    |
| Rock Salt                                            | 1      | CLEAN (2026-10-13, probe_batch.sh + land_batch.sh; plan from make_plan.py)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| Schoolbell                                           | 1      | CLEAN (2026-10-13, probe_batch.sh + land_batch.sh; plan from make_plan.py)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| Unkempt                                              | 2      | CLEAN (2026-10-13, probe_batch.sh + land_batch.sh; plan from make_plan.py)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| Walter Turncoat                                      | 1      | CLEAN (2026-10-13, probe_batch.sh + land_batch.sh; plan from make_plan.py)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| Slackey                                              | 1      | CLEAN (2026-10-13, probe_batch.sh + land_batch.sh; plan from make_plan.py)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| Sunshiney                                            | 1      | CLEAN (2026-10-13, probe_batch.sh + land_batch.sh; plan from make_plan.py)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| Permanent Marker                                     | 1      | CLEAN (2026-10-13, probe_batch.sh + land_batch.sh; plan from make_plan.py)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| PT Serif Caption                                     | 2      | CLEAN (2026-10-13); no source block; googlefontdirectory-hg keeps ParaType's own builds (ofl/ptserif/src/PTZ55F.ttf, PTZ56F.ttf)                                                                                                                                                                                                                                                                                                                                                                                                                           |
| PT Sans                                              | 4      | CLEAN (2026-10-13); no source block; no source in googlefontdirectory-hg                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| East Sea Dokdo                                       | 1      | CLEAN (2026-10-13); the designers' repository holds the fonts as built                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| Yeon Sung                                            | 1      | CLEAN (2026-10-13); the designers' repository holds the fonts as built                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| Black Han Sans                                       | 1      | CLEAN (2026-10-13); the designers' repository holds the fonts as built                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| Do Hyeon                                             | 1      | CLEAN (2026-10-13); the designers' repository holds the fonts as built                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| Stylish, Sunflower (3), Cute Font, Song Myung, Dokdo | 7      | CLEAN (2026-10-13); no source block; added as built in google/fonts#1459 (2018), no source repository known (Dokdo once glyph 0 pairs with glyph 0 in the functional gate)                                                                                                                                                                                                                                                                                                                                                                                 |
| Black And White Picture                              | 1      | CLEAN (2026-10-13) once glyph names suit a feature file; no source block, added as built in google/fonts#1459, no source repository known                                                                                                                                                                                                                                                                                                                                                                                                                  |
| Gamja Flower, Hi Melody                              | 2      | CLEAN (2026-10-13) once glyph 0 pairs with glyph 0 (an empty .notdef in a font with no glyph names); the designers' repositories hold the fonts as built                                                                                                                                                                                                                                                                                                                                                                                                   |
| Poor Story                                           | 1      | CLEAN (2026-10-13), as Gamja Flower; no source block, but yoondesign/Yoonfont-PoorStory holds the fonts as built (its upstream_info.md missed it: corrected)                                                                                                                                                                                                                                                                                                                                                                                               |
| Nanum Gothic                                         | 3      | CLEAN (2026-10-13) on the converter and gates of that day; googlefontdirectory-hg and naver/nanumfont hold the fonts as built                                                                                                                                                                                                                                                                                                                                                                                                                              |
| Nanum Brush Script                                   | 1      | CLEAN (2026-10-13, the final converter of that day) once glyph names suit a feature file                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| Lato                                                 | 18     | CLEAN (2026-10-13) once the reader marks a no-GDEF font's Mn glyphs when it attaches marks (135 marks lost before), the table gate takes HarfBuzz's Mn-only synthesis (U+0488, U+0489, U+20DD are bases), unnamed glyphs are named as fontTools names them (glyph00094) and the functional gate pairs those names in a release with no glyph names; googlefonts/LatoGFVersion holds the fonts as built                                                                                                                                                     |
| Nanum Pen Script                                     | 1      | CLEAN (2026-10-13) once the table gate compares renamed glyphs as drawn (the release's lsb is 11 where xMin is 8; 1214 rows had blocked though nothing renders differently); googlefontdirectory-hg's src/ holds NanumPen.otf, a font as built, no source                                                                                                                                                                                                                                                                                                  |

All 47 re-landed (2026-10-13, evening; `land.py <repo> --rebuild --unpublished-converter`) on
the final converter and gates of the day, after this repository's unpushed history was
rewritten to replace five local babelfont build hashes that check_publishable.py refused, so
that every landed commit cites a revision that will be published: 43 CLEAN, 4 RESIDUAL (Averia
x3, Sansation, as before). Stylish, RESIDUAL under the degenerate-point rules reverted that
day, is CLEAN again.

PT Mono is not binary-only: it has no source block, so screen.py did not scan it, but
googlefontdirectory-hg keeps ofl/ptmono/src/PTM55FT.vfb (its upstream_info.md missed it:
corrected). It probes CLEAN from its binary once the reader reads post.isFixedPitch, a
reference for its .vfb conversion. Of the other NO-REPO families only Ruslan Display has a
source in that mirror (excluded already).

make_plan.py, measuring PT Serif Caption, showed what four plans written by hand had left out:
PT Serif, PT Sans Narrow and PT Sans Caption keep a legacy kern table beside GPOS kern, which
the sources do not carry, and Oranienbaum had no plan at all (hinted; the same kern table). All
four were given the disclosure and re-landed: CLEAN.

Corrected 2026-10-13 (same day): an earlier version of this paragraph excluded Schoolbell,
Walter Turncoat, Slackey, Sunshiney, Permanent Marker, Rock Salt and Unkempt because their
upstream_info.md says "legacy formats only (.vfb/.sfd)". That is wrong: no .vfb, .sfd or other
source file is in their googlefontdirectory-hg directory at the recorded commit or anywhere in
its history (`screen.py`), nor for Ubuntu Condensed. They are binary-only. The same claim is
wrong in 16 upstream_info.md files, and 21 state a Source path that is not in the repository
(`check_info_claims.py`); the corrections go to google/fonts.

Two landed families are not binary-only (`screen.py`, which opens .zip files): Almarai's
repository (JuergenWillrodt/Almarai 7307ede5d42b) keeps its four UFO sources zipped
(source/1-drawings/Almarai-*.ufo.zip), and Dongle's (yangheeryu/Dongle f7127c4d2450) keeps
Dongle.glyphs in sources/Dongle.zip (the three .glyphs were zipped in 2021, "Updating for GF").
Their landed repositories leave this track: they are to be converted from those sources,
whichever is closest to the release. Zipped sources also hide Gowun Batang, Shippori Mincho,
Zen Antique (Soft), Zen Maru Gothic and Zen Old Mincho from a census that lists files.

Tried and reverted (2026-10-13): Kirang Haerang, Single Day and Gothic A1 each have 2 to 4
glyphs whose release contour has off-, on- and off-curve points at one place (a corner of
straight lines); the build keeps one off-curve point there and rounds the corner by under a
unit (the rendering check sees no ink difference). Dropping such off-curve points in the
reader fixed those glyphs but changed the point structure of others: Kirang Haerang went
from 4 differing glyphs to 418, and to 159 when only an off-curve point between two real
on-curve points was dropped (skrifa draws TrueType's implied on-curve points, so the reader
cannot tell them from stored ones in every case). The reader keeps its points as drawn; the
step that merges coincident points and keeps the off-curve one is still to be found.

## Re-landed again; the 36 not landed (2026-10-13, night)

The measured converter changed once more (a font with no glyph names gets `.notdef` for glyph
0, as fontTools names it; `babelfont/` as of this commit), so all 47 were re-landed: 43 CLEAN,
4 RESIDUAL (Averia x3, Sansation), every verdict as before. Their sources are the generation
before (land.py keeps it as `<repo>.prev`) except for what babelfont makes up on every run, the
`.glyphs` date and the master ids: `same_sources.py` reads SAME for all 49 repositories (the 47,
Almarai and Dongle), and DIFFERENT once one advance width in a copy is changed. Those two values
make every re-land a new source: the TTF reader gives each master `Uuid::new_v4()`
(babelfont/src/convertors/ttf.rs:176 and 196 at upstream d44f2bdc) and `Font::new` dates the
font `chrono::Utc::now()` (babelfont/src/font.rs:136). A reproducible conversion needs both
derived from the input.

The 36 binary-only families not landed were re-probed on the same converter and gates, one
at a time (`probe_batch.sh`; logs, summary.tsv and order.txt in
`results/probe-batch-2026-10-13j/`): 72 styles, 12 CLEAN, 59 RESIDUAL, 1 build failure. Then
the table gate was re-run on each style with its GSUB arbitration traced (`gate_trace.sh`,
`results/gate-trace-2026-10-13j.txt`). This table supersedes the not-landed rows above.

| families (styles)                                                                     | what blocks (measured)                                                                                                                                                                                                                                                                                                                             |
|---------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Khmer (1), Chenla (1), Content (2), Siemreap (1), Phetsarath (2), Yinmar (1)          | AAT `morx`, which HarfBuzz shapes with and fontc does not write: runs differ in Khmer 6930 of 36123, Chenla 65920 of 164482, Content and Siemreap 80272 of 164513, Phetsarath 2535 of 29332 (Bold 29347), Yinmar 19621 of 80657. Also `feat` (all), `prop` (Chenla, Content, Siemreap), VTT sources TSI0-3 and TSI5 (Phetsarath Bold), D6 (Yinmar) |
| the 10 IM Fell families (15)                                                          | 246 to 255 runs per style, all with U+0326; head.font_direction_hint 0 (decision D6, open); GSUB rows the gate does not clear (gap B below). Felipe's decision (bottleneck 8)                                                                                                                                                                      |
| Alef (2), Nanum Gothic Coding (2), Nanum Myeongjo (ExtraBold; Bold and Regular CLEAN) | head.font_direction_hint 0 only (D6)                                                                                                                                                                                                                                                                                                               |
| Gulim (1), GulimChe (1), Dotum (1), DotumChe (1)                                      | head.font_direction_hint 1 (D6); vhea version 1.0 against 1.1, and (but Gulim) its minBottomSideBearing and yMaxExtent; GSUB `vert` rows the gate does not clear (gap C)                                                                                                                                                                           |
| Ek Mukta (7)                                                                          | GSUB rows only (gap A); functional gate PASS                                                                                                                                                                                                                                                                                                       |
| Carlito (4)                                                                           | GDEF.glyph_classes only (gap D); functional gate PASS                                                                                                                                                                                                                                                                                              |
| Jomolhari (1)                                                                         | GSUB rows (gap A) and `PCLT` (gap E); functional gate PASS                                                                                                                                                                                                                                                                                         |
| Uchen (1)                                                                             | GSUB rows (gap A); 60 of 5587232 runs differ (28 of 2286 rule runs; 4 words; 28 with `rlig` off), not investigated                                                                                                                                                                                                                                 |
| Kirang Haerang (1), Single Day (1), Gothic A1 (SemiBold, Thin; the other 7 CLEAN)     | the corner points above: 4, 2 and 1 codepoint(s) map to a glyph drawn differently (by under a unit)                                                                                                                                                                                                                                                |
| Gaegu (Light; Bold and Regular CLEAN)                                                 | hmtx: uniFF15's outline differs by 1 unit (left bearing 254 against 255)                                                                                                                                                                                                                                                                           |
| Anonymous Pro (4)                                                                     | bitmap strikes (EBDT, EBLC, EBSC), which a .glyphs source cannot carry (post.isFixedPitch is read now)                                                                                                                                                                                                                                             |
| Averia Gruesa Libre (1)                                                               | italic angle -1.7 on an upright font: the build names it Italic and sets fsSelection ITALIC; GPOS rows                                                                                                                                                                                                                                             |
| GFS Didot (1)                                                                         | `grek` registered without features (see above): 20624 of 1848234 runs differ                                                                                                                                                                                                                                                                       |
| GFS Neohellenic (Regular, Bold, Italic; BoldItalic CLEAN)                             | Regular: only gap F. Bold: gap F, GPOS rows, 8740 of 9191 base+mark runs differ. Italic: 33893 of 996700 runs differ (61 of 315565 pairs). Not investigated                                                                                                                                                                                        |
| Datatype (1)                                                                          | the one variable font: land.py's config builds statics (`buildVariable: false`), and instantiating SemiBold fails ("No master was present at location ... wght: 600.01")                                                                                                                                                                           |

Gaps in the gates, measured (`gate_trace.sh`, `gsub_lookups.py`, `gdef_classes.py`):

- A. table_gate.py's GSUB lookup-order arbitration refuses every font with a multiple
  substitution: `profile()` keys each mapping's value as one glyph, a multiple substitution maps
  to a list, and the TypeError is caught as a refusal (9 styles: Ek Mukta, Jomolhari, Uchen).
  Jomolhari's release and build have the same 25 lookups; the release lists four nested single
  substitutions after the four chaining lookups that call them, fontc puts each before its caller.
- B. The same arbitration compares x advances. HarfBuzz applies a legacy `kern` value split
  between the two glyphs (half as the second one's offset) and GPOS kerning on the first, so IM
  Fell English SC's `'A` reads 518 + 1341 against 479 + 1380: the same total, the A drawn at the
  same place. All 15 IM Fell styles refuse this way.
- C. A `vert` lookup never fires in its horizontal corpus ("the corpus never fired the
  features"), although Gulim's release and build carry the same 32 `vert` substitutions keyed by
  codepoint.
- D. GDEF glyph classes are compared by name. A release with no glyph names (post format 3) is
  named by fontTools (AGL names) and the build `uniXXXX`, so Carlito's 479 renamed glyphs read as
  base in the release and unclassified in ours, while the classes are equal glyph by glyph.
- E. Jomolhari keeps a `PCLT` table (HP PCL printer metrics), which fontc does not write; the gate
  has no rule for it (it accepts VDMX, LTSH, hdmx and DSIG).
- F. The functional gate's cmap check fails a rename the build cannot avoid: GFS Neohellenic names
  U+2116's glyph `Numero sign`, with a space; the build calls it `Numero_sign` (same outline and
  advance). A name the release gives several glyphs is noted, not failed, for the same reason.

Ek Mukta's and Carlito's only blocking rows come from gaps A and D.

Gaps A, B and D are now closed in table_gate.py: a multiple
substitution is profiled as a glyph-to-sequence rule; the arbitration compares where each glyph
is drawn and where the run ends; GDEF is compared glyph id by glyph id when both fonts keep
one glyph order (same glyph count, every shared codepoint on the same id). The table gate
re-run on the same builds (`results/gate-trace-2026-10-13j-fixed.txt`): Ek Mukta (7) and Carlito
(4) block on nothing, and the functional gate passes them; IM Fell blocks on
head.font_direction_hint alone (with U+0326 in the functional gate); Jomolhari on `PCLT`;
Uchen's GSUB rows clear, its 60 shaped runs remain. C, E and F are open; E (`PCLT`) is
Felipe's call.
