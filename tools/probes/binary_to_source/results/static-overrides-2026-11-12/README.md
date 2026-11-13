# Binary-route probe of the static-only overrides that need source work (2026-11-12)

Question: for the four families whose google/fonts override config cannot reproduce what ships (Kumar One, Kumar One Outline, Hind Colombo, Poppins; found while reviewing google/fonts#11277), does converting the shipped TTFs give a source that rebuilds them?

    BF=<babelfont> B3=<gftools-builder> python3 tools/probes/binary_to_source/probe.py <scratch> <shipped .ttf>...

Tools: babelfont main f1458803 merged with the branches glyphs3-unmapped-axes and ttf-instance-user-coords (neither touches a static font) and skrifa 0.46.2 patched as in ../reprobe-2026-11-12/reader-fixes; gftools-builder from the head of simoncozens/gftools-rust#2. Shipped fonts: google/fonts e77406770. Output: `probe.txt`.

| font(s)                                   | functional checks                                                              | table rows                              |
|-------------------------------------------|--------------------------------------------------------------------------------|-----------------------------------------|
| KumarOne-Regular, KumarOneOutline-Regular | FAIL gdef (GDEF absent in the build), hinting (prep, gasp); the other six pass | 3 (GSUB script, feature, lookup lists)  |
| HindColombo, 5 styles                     | FAIL shaping (2412 or 3329 of 893180 runs), rendering (6 words), line_spacing (WWS bit), gdef, hinting (ttfautohint); Light, Medium, SemiBold also names (ID 16, 21) | 2 (GSUB) |
| Poppins-Regular, Poppins-Italic           | PASS                                                                           | 3 (GSUB)                                |
| Poppins-Black                             | FAIL names (ID 16, 21); the other seven pass                                   | 3 (GSUB)                                |

Only 3 of Poppins's 18 styles were probed. The probe does not apply a landing plan: land.py's GDEF classes and hinting route would address Kumar's two failures; the name IDs 16/21 are what the babelfont branch typographic-family-names fixes.

Why the upstream Glyphs sources do not reproduce the shipped fonts (repo archive, at the METADATA.pb commits):

- itfoundry/kumar 3192a79: one file, masters "Filled" and "Outlined" (the two families), no instances, features in separate .fea files; built with hindkit + AFDKO.
- itfoundry/hind-colombo 3cf4e8b: 251 Sinhala glyphs; the shipped fonts have 588 (hindkit imported the Latin from elsewhere).
- itfoundry/Poppins 738d9d6: Latin and Devanagari in two files that hindkit merged; gftools builds them as two families with numeric style names.

Decision (Felipe, 2026-11-12): Kumar One: measure the Glyphs-source route too before choosing; Hind Colombo and Poppins: recorded, no conversion now.

## Kumar One: both routes measured (2026-11-12)

Glyphs-source route at the old pin (3192a79, release 1.001): not possible. That file has 847 glyphs; the shipped font has 868 (22 glyphs and U+0AF9 are not in the file). Superseded on 2026-11-13: google/fonts#11312 moved the pin to [itfoundry/kumar 551e277f](https://github.com/itfoundry/kumar/tree/551e277f8fc8f18a5ee11935cf5007bda9930364) (release 1.000), whose file has the shipped 868 glyphs. See "Glyphs route at the new pin" below.

Binary route, measurement landings (`landing/`: families.tsv, plans, logs; land.py with BF_TREE = babelfont f1458803 + typographic-family-names, B3 = gftools-rust#2 head, HINTING_EXTRACT = gftools#1248 head; scratch only): both families RESIDUAL, 3 GSUB table rows, functional FAIL(gdef+hinting); cmap, shaping (756602 and 759446 runs, 0 differ), rendering, names, line spacing and advances pass. The two failures:

- gdef: the release has a GDEF table in which 18 marks are unclassified; the build has no GDEF, so shaping reads them as marks. The plan's `gdef_classes_fea` did not produce a table.
- hinting: prep (127 bytes), fpgm and gasp are now equal to the release's; the gate still reports "the build is instructed (0 glyph programs, fpgm 265 bytes), the release is not".


## Kumar One: Glyphs route at the new pin (2026-11-13)

Question: does itfoundry/kumar's Glyphs file at the pin google/fonts#11312 set rebuild the shipped fonts? Scripts and output in `glyphs-route-2026-11-13/`:

| script            | question it answers                                                                 |
|-------------------|-------------------------------------------------------------------------------------|
| split_masters.py  | one single-master file per family (masters Filled, Outlined)                        |
| prepare_source.py | what the file lacks that hindkit + AFDKO supplied at build time; prints each edit   |
| gate_source.py    | gates a build of the prepared source as probe.py does (BUILT=<ttf> skips the build) |
| outline_area.py   | signed area and bounds per glyph, build vs shipped                                  |

    python3 split_masters.py "masters/Kumar One.glyphs" split
    python3 prepare_source.py split/KumarOne.glyphs features KumarOne-Regular.ttf src/kumarone/sources/KumarOne.glyphs
    fontc src/kumarone/sources/KumarOne.glyphs --no-production-names -o KumarOne-Regular.ttf
    BUILT=KumarOne-Regular.ttf python3 gate_source.py <gf-source-modernization> <work dir> <shipped KumarOne-Regular.ttf>

Tools: glyphsLib 6.17.1 (split, prepare); fontc 2.0.1 at 5715ced0 (fea-rs 2.0.0); the gates of this repository as of this commit; shipped fonts: [google/fonts 3e566776](https://github.com/google/fonts/tree/3e5667764ccfea32ce0c3d58a3a4756de890adc1). gftools-builder (gftools-rust#2 head, fontc 1.0.0) cannot build the source: fea-rs 1.0.0 panics in compile/lookups/contextual.rs:379 on lookup `abvs_ra_matra_vocalic_liquids`.

Edits prepare_source.py makes: an instance "Regular" (the file has none); 4 glyphs renamed as GlyphOrderAndAliasDB does (Acaron, acaron, Ocaron, ocaron); codepoints on 12 glyphs (11 combining marks lose theirs, gjZHA gets U+0AF9); the shipped glyph order; features/GSUB_lookups.fea + GSUB.fea behind the shipped language systems; kerning removed (the shipped fonts have no GPOS).

| check                  | Kumar One                                   | Kumar One Outline                            |
|------------------------|---------------------------------------------|----------------------------------------------|
| verdict                | RESIDUAL, 17 table rows                     | RESIDUAL, 20 table rows                      |
| cmap, advances         | PASS (408 codepoints; 797 advances)         | PASS                                         |
| names                  | PASS                                        | FAIL: ID 4 "Kumar One Outline Regular"       |
| shaping                | FAIL: 528 of 756602 runs (base+mark)        | FAIL: 1210 of 759450 runs                    |
| rendering              | FAIL: 65 glyph outlines draw different ink  | FAIL: 242 glyph outlines draw different ink  |
| line spacing           | FAIL: typo/hhea/win 1137/-642 vs the file's | FAIL: same                                   |
| gdef                   | FAIL: 25 classes (shipped leaves marks unclassified) | FAIL: 25                            |
| hinting                | FAIL: prep and gasp absent in the build     | FAIL: same                                   |

What the outline differences are (outline_area.txt): 372 (Kumar One) and 805 (Outline) of 868 glyphs differ in signed area, but all except 7 have equal bounds, and 682 of the Outline's have the opposite sign. So the drawings are the same; the shipped fonts had overlaps removed and contour direction corrected at build time. The 7 are combining marks that the build moved to negative side bearings (hookabovecomb: x 121..321 in the file, -300..-100 shipped).

Reading: the file is the right source, and everything else is build-time processing by hindkit + AFDKO: overlap removal and direction, mark repositioning, vertical metrics (also the google/fonts hotfix), GDEF, prep/gasp, OS/2 values. The binary route needs none of that (3 GSUB table rows, gdef and hinting only), so it remains the closer one.
