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

Glyphs-source route: not possible from what is published. itfoundry/kumar 3192a79 (its only branch head) has 847 glyphs and its own products/KumarOne-Regular.ttf has 847. The shipped font is google/fonts 06463af09 ("hotfix-kumarone: v1.001 added", #973, 2017): 868 glyphs. 22 of them are not in the Glyphs file (gjCH, gjD, gjDD, gjTT, gjTTH, gjJH and ligatures of them), it maps U+0AF9, which the file does not, and the file maps 11 combining marks (U+0302 ... U+0328) that the shipped font does not. The features are in separate .fea files and the file has no instances (probe: research-scratch sessions/2026-11-12_static-overrides-source-work/split_masters.py; a split single-master file gives gftools "No final targets").

Binary route, measurement landings (`landing/`: families.tsv, plans, logs; land.py with BF_TREE = babelfont f1458803 + typographic-family-names, B3 = gftools-rust#2 head, HINTING_EXTRACT = gftools#1248 head; scratch only): both families RESIDUAL, 3 GSUB table rows, functional FAIL(gdef+hinting); cmap, shaping (756602 and 759446 runs, 0 differ), rendering, names, line spacing and advances pass. The two failures:

- gdef: the release has a GDEF table in which 18 marks are unclassified; the build has no GDEF, so shaping reads them as marks. The plan's `gdef_classes_fea` did not produce a table.
- hinting: prep (127 bytes), fpgm and gasp are now equal to the release's; the gate still reports "the build is instructed (0 glyph programs, fpgm 265 bytes), the release is not".
