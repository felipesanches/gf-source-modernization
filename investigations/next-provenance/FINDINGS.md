# next-provenance -- investigation findings

**Model**: Claude Opus 5.5 (investigating agent, adversarial verifier, and the
conclusion below). Written from the agents' structured results (`results.json`).

## Conclusion

Lohit's METADATA commit is another family's tag: Bengali and Tamil re-pair to 0df83ad and
361b23b. Thabit is build.py's output (the 2010 .sfd + Thabit.fea + IBM Courier, obliques
generated) and needs its steps as documented edits plus several babelfont exporter
filters. Yellowtail's ".sfd" is a Type 1 file: out of the SFD programme. The verifier
found functional gaps the table gate hides (Lohit-Bengali renders 284 words differently;
USE_TYPO_METRICS set where FontForge did not), which is why a functional gate is needed.

## Investigator's report

Provenance is settled for all four families from byte identity, FFTM stamps and file
headers. Lohit is revision drift: METADATA's commit is another family's tag. Thabit is a
build script merging IBM Courier and a .fea into a later (2010) save of the 2008 source,
with generated obliques. Yellowtail's '.sfd' is a Type 1 file from the FontForge session
that exported the release. Every proposed .sfd edit and converter change was measured
with tools/baseline.sh (FAMILIES=..., BF=the prototype, SRC_OVERRIDE, EXTRA_FLAGS) plus
land.py's workaround, and on the rendering diff (probes/d3_render.py). Two 149-style
regression sweeps (batch 1 and next batch) compared the prototype plus 4 filters with
unpatched 17ea899: no table-row regressions; improvements in Tuffy-Italic, Cardo-Italic
and Lohit-Tamil; rendering churn only in Tuffy-Regular (not a FontForge export) and
Ultra.

Rows before: Lohit-Bengali 1; Lohit-Tamil 8; Thabit 465; Thabit-Bold 465; Thabit-Oblique and Thabit-BoldOblique unpaired (465 each measured against the upright source); Yellowtail-Regular unpaired (no convertible source)

Rows after: Lohit-Bengali 0 at 0df83ad, but 284 Bengali words still render differently. Lohit-Tamil 0 at 361b23b with the spacing-combining fix, and 0 glyph / 0 word rendering diffs. Thabit, Thabit-Bold, Thabit-Oblique and Thabit-BoldOblique: 3 each from the harness, 2 with land.py's workaround (PfEd, head.font_direction_hint), 0 with the gate change. Their Arabic rendering is exact in the uprights; in the obliques it differs only through release-stale lsb, with identical shaping; the Latin keeps the cu2qu residue. Yellowtail: not applicable.

Confidence: High on provenance for all four families: byte identity with the Arabeyes 0.02 TTFs, FFTM sourceModified equal to the .sfd ModificationTime, the PFB header matching FFTM sourceCreated, and the X.Org PFAs byte-identical to hg's. High on the Lohit-Tamil fix: exact, 0/0 rendering diffs. High on the causes of each Thabit table row, each closed by a measured step; the Arabic rendering is exact in the uprights and differs only through release-stale lsb in the obliques. Medium on the Thabit reconstruction as a whole: the 0.02 helper.py is lost, the 2008 .sfd is lost, the Latin uses a cu2qu stand-in, and the AFMs are an inferred input. Medium-high that the babelfont changes are safe: two 149-style sweeps showed no table regressions, but they are unreviewed prototypes, and the FontForge-exporter filters should be gated on FFTM. Low confidence that Lohit-Bengali is equivalent despite its CLEAN table-gate result.

## Rows

| style | row | class | cause |
|---|---|---|---|
| Lohit-Bengali | OS/2.panose_10 {"1": [0, 11]} | provenance | The pairing and google/fonts METADATA use pravins/lohit a403c9b. That commit is the lohit-gujarati-2.92.1 tag (2013-12-12), which a 'tag_match' heuristic took from another family in the monorepo. The release was built from the 0df83ad state. Its FFTM sourceModified is 1330511755 (2012-02-29 10:35:55 UTC), which equals the .sfd ModificationTime at 0df83ad and at 9d61e32. Its name ID 5 is 'Version 2.5.1' and its PANOSE is 2 0 6 ... . That PANOSE matches 0df83ad; 9d61e32 ('updated panose value') changed it to 2 11 6 without re-saving the file. By 8b3650e the .sfd is 2.5.3 (a403c9b has 2.5.3). |
| Lohit-Bengali | RENDERING (not a table-gate row): 284 Bengali words differ, up to 801 px, while the table gate reports CLEAN | converter-fidelity | Below- and above-base marks are not positioned (u09C1, u09C2, u09C3, u0981, reph). The release's GPOS is abvm = [mark-to-base with 240 bases, chain lookup 2] and blwm = [mark-to-base]. babelfont leaves the .sfd's anchor lookups to fontc's mark writer, but it writes the chain lookup "'abvm' Above Base Mark in Bengali lookup 2" as a declared feature abvm. fontc does not generate a feature the source already declares, so our GPOS is abvm = [chain] and mark = 3 mark-to-base lookups with only 5 bases (uni25CC and glyphNNN). The table gate calls the GPOS difference RELEASE-STALE ('organised differently'), and neither baseline.sh nor land.py gates the rendering diff. The fault is in the converter, not in the pairing: the same 288 words differ at a403c9b. |
| Lohit-Tamil | hmtx.u0BEA, hmtx.u0BEC, hmtx.u0BED, hmtx.u0BEE, hmtx.u0BEF, OS/2.panose_10 | provenance | The pairing commit a403c9b is wrong here as well. The release was built from the 361b23b state: FFTM sourceModified 1316598937 (2011-09-21 09:55:37 UTC) equals the .sfd ModificationTime at 361b23b, and the version is 2.5.0. After that, 723f00c (2012-04-25) widened the Tamil digits (u0BEA 663->746, u0BEE 1020->1142) and 9d61e32 changed the PANOSE. |
| Lohit-Tamil | hmtx.u0BC1 {"width": [532, 0]}, hmtx.u0BC2 {"width": [776, 0]} | converter-fidelity | babelfont's SFD reader gives every GlyphClass:4 glyph the Glyphs subCategory Nonspacing (fontforge.rs, upstream since #66). fontc exports a Nonspacing mark with zero width (glyphs-reader 1.0.0 Glyph::is_nonspacing_mark; glyphs2fontir 1.0.0 source.rs:1829). FontForge writes the advance the source states (Width 532/776). A Mark with subCategory Spacing Combining keeps both its GDEF mark class (category_for_glyph_preliminary) and its advance. |
| Thabit, Thabit-Bold | cmap x458 LOST (U+0021-U+007E, Latin-1, Latin Extended-A, Greek, SF*/SM*/SS*/SV* box drawing, U+FB00-FB04 ...) | provenance | The Latin comes from the build script, not from the .sfd. build.py (helper.py in the 0.02 ChangeLog) runs font.mergeFonts('cour/cour.pfa') (courb.pfa for Bold), which adds the IBM Courier Type 1 fonts in src/cour/. The .sfd has no Latin: the 2008-08-09 ChangeLog says 'Removed non-arabic glyphs'. FontForge 2008 _MergeFont (fvfonts.c at eb711fd7) copies glyphs unscaled: A has advance 600 in the 1024-em font. It names them by FontForge's own UniFromName (namelist.c psaltnames: SM680000->U+2310, ohm->U+2126, micro->U+00B5, dbar->U+0111, Pts->U+20A7). fontTools' AGL leaves 33 of these different. |
| Thabit, Thabit-Bold | GSUB.script_list, GSUB.feature_list, GSUB.lookup_list (release: rlig/init/medi/fina/liga arab + liga latn; ours: none) | provenance | Five of the six lookups come from build.py's font.mergeFeature('Thabit.fea'): rligTashkilLigatures, InitialForms, MedialForms, FinalForms and ligaLamAlef. The sixth is a latn liga lookup that FontForge's AFM reader created from the IBM Courier AFM's L lines (LoadKerningDataFromAfm). The release's PfEd names that lookup "Courier-'liga' Standard Ligatures in Latin lookup 0". Its rules equal X.Org font-ibm-type1 cour.afm ('N f ; L f ff ; L i fi ; L l fl', 'N ff ; L i ffi ; L l ffl'). The AFMs are not in the hg tree. |
| Thabit, Thabit-Bold, Thabit-Oblique, Thabit-BoldOblique | OS/2.us_weight_class [500, 400] (Bold and BoldOblique: [700, 400]) | compiler-gap | fontc 1.0.0 ignores a single master's instance weightClass. The .sfd states TTFWeight 500 or 700. This is the known issue in issues/fontc-static-weight-class.md. |
| Thabit, Thabit-Bold, Thabit-Oblique, Thabit-BoldOblique | PfEd: whole-table difference | gate-arbitration | PfEd is FontForge's private table. In these releases it holds only the GSUB/GPOS lookup, subtable and anchor-class names (decoded: rligTashkilLigatures, ... "Courier-'liga' ...", ArabicAbove, ...). No shaper or rasterizer reads it, fontc does not write it, and the gate already accepts FontForge's other private table, FFTM. |
| Thabit, Thabit-Bold, Thabit-Oblique, Thabit-BoldOblique | head.font_direction_hint [0, 2] | gate-arbitration | FontForge 2008 tottf.c sethead writes 0 for a font with both LTR and RTL glyphs ('if ( lr && rl ) head->dirhint = 0;'); Thabit is Arabic plus Courier. The OpenType spec deprecates the field ('set to 2'), no Glyphs parameter can state it, and fontc writes 2. The same row appears for Cardo-Bold and Cardo-Italic (Hebrew plus Latin). |
| Thabit, Thabit-Bold | hmtx.2, .notdef member (release lsb 34 / advance 374; ours 51 / 512) | converter-fidelity | The .sfd has no .notdef. FontForge's TTF exporter synthesises one (tottf.c dumpmissingglyph): stem = (a+d)/30 = 34, ymax = 682, xmax = 306, advance 374. That is exactly the release's glyph. This is the same rule as the Tuffy precedent. |
| Thabit, Thabit-Bold | hmtx.2, uni06D4 member (release lsb 186, ours 187) | converter-fidelity | The .sfd states half-unit points (186.5 0 m). FontForge's SSAddPoints writes glyf points with rint(), which rounds ties to even (186). fontc rounds half up (187). There are 1574 half-unit coordinates in 102 glyphs. |
| Thabit (rendering, all styles) | 44 Arabic words: lam-alef not formed across harakat, marks unattached on lam-alef ligatures | converter-fidelity | Two converter defects. (a) babelfont writes lookupflag only for contextual lookups (the has_chain branch, upstream since #78), so ligaLamAlef loses RightToLeft/IgnoreMarks (SFD flag 9) and every ordinary GSUB/GPOS lookup loses its flags. (b) babelfont names 'baselig <n>' anchors with the bare class name, which duplicates it, so fontc cannot build mark-to-ligature. Glyphs names them <class>_<n+1>. |
| Thabit-Bold (rendering) | 1 Arabic word: shaddahdammah attached to uniFBFE in ours, not in the release | converter-fidelity | In Thabit-Bold.sfd uniFBFE is only a reference (to gid 179) and has no anchors. FontForge exports a glyph's own anchors only. fontc propagates anchors from components unless the font sets the custom parameter 'Propagate Anchors' to false. |
| Thabit-Oblique, Thabit-BoldOblique (rendering) | Arabic mark offsets 1-2 units apart | converter-fidelity | FontForge's dumpanchor writes anchors with putshort(gpos, ap->me.x), which truncates toward zero. fontc rounds. The skew makes every anchor fractional. |
| Thabit, Thabit-Bold, Thabit-Oblique, Thabit-BoldOblique (rendering) | 60-83 Latin/Greek/symbol glyph diffs (<=46 px) and 121-140 Latin words (<=108 px) | converter-fidelity | FontForge's merge converts each copied Type 1 glyph to the order2 layer with splineorder2.c SplineSetsTTFApprox (fvfonts.c SplineCharCopy -> SCConvertOrder). The mergepsfont probe uses cu2qu (max_err 1) instead, so the points differ from FontForge's and the areas differ by up to 0.2% (e.g. 'o' 71478 vs 71613). Contour reversal (psread.c) and naming are exact. |
| Thabit-Oblique, Thabit-BoldOblique | no source (UNPAIRED); against the upright source: 465 rows each | provenance | The obliques are generated at build time: build.py obliqize() then deobliqize() then generate() with couri.pfa or courbi.pfa. The release confirms every step. The skew is psMat.skew(-16) in RADIANS, x' = x - 0.30063 y; measured -0.3007. U+200C..U+202E (afii61664..afii61575) are deselected and stay upright. References are unlinked. Upright Courier ( ) [ ] { } ! are pasted in, and the release shows them unskewed with the upright lsb. PfEd names the lookup "Courier-Italic-'liga'..." (Courier-BoldItalic in BoldOblique). |
| Thabit-Oblique, Thabit-BoldOblique (rendering) | 1 and 15 Arabic glyph diffs; 6 and 7 Arabic words whose shaping is identical | gate-arbitration | This is a release inconsistency no source can reproduce. FontForge 2008 writes the glyf bbox from curve extrema and the hmtx lsb as the unrounded minx truncated to int (tottf.c ttfdumpmetrics putshort(gi->hmtx, b->minx)). As a result 156 and 228 glyphs carry an lsb different from their own xMin. Examples: kafinitial has lsb -56 with xMin -57; tehring has header xMin -29 while its points reach -32. A rasterizer places the glyph by the lsb, so it draws one unit off. Our point sets are identical to the release's (kafinitial 41 = 41 points). |
| Thabit, Thabit-Bold (names; not gated) | family 'Regular Medium'/'Bold' in our build vs 'Thabit' in the release; copyright, designer and name IDs 8/9/16/18 | provenance | The .sfd drifted after the release, and the release's own source state is lost. Shipped Thabit.ttf is byte-identical to the Arabeyes Thabit-0.02 release (SourceForge Fonts/Thabit 0.02/Thabit-0.02.tar.gz, built 2008-08-09). The other three styles differ from that release only in name ID 4 (Raph Levien's FixName, hg 465c5490a + 49339cae0, 2011-12-15). The hg .sfd files were saved again on 2010-06-15 (ModificationTime 1276640170 / 1276640219), with Copyright 2008-2010, FamilyName 'Regular'/'Bold' and new LangName credits. The ChangeLog is unchanged since 0.02, and the drawing is unchanged: 0 Arabic rendering diffs in the uprights. The 2008-08-09 .sfd has not been found anywhere: not in hg, not in the repo archive, and the SourceForge tarballs ship only TTFs. |
| Yellowtail-Regular | UNPAIRED: src/Yellowtail-Regular-TTF.sfd 'declares no glyphs' | provenance | The file is not an SFD. It is a Type 1 PFB ('%!PS-AdobeFont-1.0: Yellowtail 001.001', 'Generated by FontForge 20110222', Creator Dave Crossland, CreationDate Mon Jul 18 09:51:27 2011); babelfont reports 'Not an SFD file'. The shipped TTF is the FontForge 20110222 export from the same session. Its FFTM sourceCreated = sourceModified = 2011-07-18 12:51:27 UTC, which is the PFB CreationDate at -0300. That export is hg 60268f00f, Dave Crossland's 'Reducing Yellowtail filesize by 30% by stripping hints and using the magic values': outlines simplified from the designer's 2011-07-17 TTF (hg f66bfe1e9), hints dropped, kern/GPOS dropped. google/fonts 1baf54ea4 (PR #803, Marc Foley, 2017, empty body) later changed only name IDs 3/4/5/6 and head.modified/fontRevision to make v1.002. The PFB matches the shipped outlines: 365 of 366 codepoints within 0.1% area and 366/366 bbox within 1 unit. The designer TTF and OTF do not: 18 and 23 codepoints are 0.4% or more off. |

## Proposed .sfd edits

- **Merge Thabit.fea into the source, as build.py does** (Thabit, Thabit-Bold, Thabit-Oblique, Thabit-BoldOblique) `mergefea src/Thabit.fea` -- verified: True; value from: src/Thabit.fea in the same tree (hg 52f780b ofl/thabit/src). The lookup and subtable names are confirmed by the release's PfEd table.; the source stated: no GSUB lookup; only 'mark' Mark to base and Mark to ligature (GPOS)
- **Add the IBM Courier AFMs FontForge read beside cour/*.pfa** (Thabit, Thabit-Bold, Thabit-Oblique, Thabit-BoldOblique) `add file src/cour/cour.afm, courb.afm, couri.afm, courbi.afm from X.Org font-ibm-type1 88a51daabc8a5bf2dbb2ace89c638058b01b3cf3` -- verified: True; value from: gitlab.freedesktop.org/xorg/font/ibm-type1 at 88a51da (sha1s in runs/thabit_release_inputs.txt). That the release used them is inferred from the PfEd lookup name and the identical ligature set.; the source stated: src/cour/ holds only LICENSE.txt, README.txt and the four .pfa files
- **Merge IBM Courier into the source, as build.py does** (Thabit (cour), Thabit-Bold (courb), Thabit-Oblique (couri), Thabit-BoldOblique (courbi)) `mergepsfont src/cour/cour.pfa src/cour/cour.afm Courier   (Bold: courb.* Courier-Bold; obliques: couri.* Courier-Italic, courbi.* Courier-BoldItalic)` -- verified: True; value from: src/cour/*.pfa (same tree) and the AFMs above; the source stated: 308 glyphs (Bold 310), Arabic only
- **Generate the oblique sources as build.py does** (Thabit-Oblique, Thabit-BoldOblique) `obliqize -16 200C 202E, then pastepsglyphs src/cour/cour.pfa src/Thabit.sfd -> src/Thabit-Oblique.sfd; src/Thabit-Bold.sfd -> src/Thabit-BoldOblique.sfd` -- verified: True; value from: build.py obliqize/deobliqize (hg 52f780b), checked against the release: skew measured -0.3007, parentheses unskewed with the upright lsb; the source stated: no oblique source exists
- **Credit IBM for the Latin, as build.py does** (Thabit, Thabit-Bold, Thabit-Oblique, Thabit-BoldOblique) `setfield Copyright <current value>\nLatin glyphs are Copyright (c) IBM Corporation 1990,1991.` -- verified: False; value from: build.py (hg 52f780b); the source stated: Typeface and data (C) 2008-2010, Khaled Hosny.\nThis font is distributed under the terms of OFL license.
- **Restore the family name Thabit** (Thabit, Thabit-Bold) `setfield FamilyName Thabit` -- verified: True; value from: release name ID 16 'Thabit' (Thabit.ttf and Thabit-Bold.ttf), name ID 1 'Thabit' (Thabit.ttf), google/fonts METADATA family 'Thabit'; the source stated: FamilyName: Regular / FamilyName: Bold

## Proposed tool changes

- **families-next.tsv / tools/pair_next.py**: Re-pair lohitbengali to pravins/lohit 0df83ad734a061144754601fc4984f72e3636108 and lohittamil to 361b23b171eef00fe33371be5b6b117b05b315c3. More generally, when the release carries FFTM, pair_next.py should check METADATA's commit against the commit whose .sfd ModificationTime equals the release's FFTM sourceModified, and flag any mismatch. For Lohit, METADATA's a403c9b came from a 'tag_match' on another family's tag.

  Evidence: runs/fftm_source_commit.txt. Lohit-Bengali goes from 1 row to 0 and Lohit-Tamil from 8 to 2 (runs/r1-lohit-provenance).
  Upstream: no (workspace). The google/fonts METADATA commit correction for ofl/lohitbengali and ofl/lohittamil is Felipe's PR.
- **babelfont-rs (SFD reader)**: When a GlyphClass:4 glyph states a non-zero Width, give it subCategory 'Spacing Combining' instead of 'Nonspacing'. It then keeps its GDEF mark class and its advance, as FontForge exported it.

  Evidence: Lohit-Tamil goes from 2 rows to 0 with 0/0 rendering diffs (runs/r2, runs/r5). The next-batch sweep (runs/regnext-compare.txt) shows it also closes 4 hmtx rows of Cardo-Italic, but opens 2 there (GDEF.glyph_classes, GDEF.mark_glyph_sets): fontc's kern writer now puts the spacing marks in a mark filtering set, while the release's kern lookup has flag 0. Cardo-Italic goes from 10 rows to 8.
  Upstream: babelfont-rs: new PR, or fold into the open FontForge reader PR. SetSubcategory should also not overwrite 'Spacing Combining'.
- **babelfont-rs (SFD reader, FEA emission)**: Write lookupflag (the 4 low bits) for every converted lookup, not only contextual ones. Today the has_chain branch is the only place the flag is written (upstream since #78).

  Evidence: Thabit's ligaLamAlef (SFD flag 9) lost IgnoreMarks and lam-alef stopped forming across harakat. Together with the baselig change, Arabic word diffs go from 44 to 0 (runs/t4 -> t5 -> t6). No table-row change in the 149-style sweeps.
  Upstream: babelfont-rs: new PR
- **babelfont-rs (SFD reader, anchors)**: Name an SFD 'baselig <n>' anchor <class>_<n+1>, the Glyphs ligature-component convention, so fontc builds mark-to-ligature.

  Evidence: Marks on Thabit's lam-alef ligatures were unpositioned; this closes them (runs/t5 -> t6)
  Upstream: babelfont-rs: new PR
- **babelfont-rs (filter)**: --fontforge-rint-coordinates: round the points of quadratic layers half to even, as FontForge's SSAddPoints does with rint(). On-curve points half-way between two off-curve points are left for the compiler to imply.

  Evidence: Thabit hmtx uni06D4 closes (runs/t6 -> t7) and so does the dalring rendering diff. The first version, which also rounded implied points, made Lekton-Bold differ in one word; the final version does not (runs/reg-batch1-compare-all7.txt).
  Upstream: babelfont-rs: add to the FontForge-fidelity filter group (open PRs #91-#93 or new)
- **babelfont-rs (filter)**: --fontforge-implied-oncurves: drop the quadratic on-curve points FontForge leaves out of glyf. These are points with no TrueType number (SFD ttfindex -1) within 0.1 unit of the midpoint of their control points, not roundx/roundy/dontinterpolate (tottf.c SSAddPoints plus SPInterpolate).

  Evidence: The glyf point sets now equal the release's (kafinitial goes from 44 points to 41, runs/p1). Tuffy-Italic loses 2 rows (26 -> 24) in the batch-1 sweep.
  Upstream: babelfont-rs: new PR
- **babelfont-rs (filter)**: --fontforge-truncate-anchors: truncate anchor coordinates toward zero, as FontForge's dumpanchor does with putshort(ap->me.x).

  Evidence: After it, every remaining Arabic word diff in the obliques has identical shaping: 6/6 and 7/7 (runs/p2, p3)
  Upstream: babelfont-rs: new PR
- **babelfont-rs (filter)**: --fontforge-no-anchor-propagation: set the Glyphs custom parameter 'Propagate Anchors' to false, which fontc honours (glyphs2fontir source.rs). FontForge exports only a glyph's own anchors.

  Evidence: The Thabit-Bold word with shaddahdammah on the reference-only uniFBFE closes (runs/p2 -> p3)
  Upstream: babelfont-rs: new PR
- **babelfont-rs (filter)**: --fontforge-notdef: synthesise FontForge's .notdef (tottf.c dumpmissingglyph) when the .sfd has none. This is Tuffy's proposal, confirmed here.

  Evidence: The Thabit .notdef hmtx member closes with the emulation (runs/t1-thabit-merged -> t1-thabit-merged-notdef)
  Upstream: babelfont-rs: new PR (not implemented)
- **tools/recipe.py**: Pass the five FontForge-exporter filters (rint, implied-oncurves, truncate-anchors, no-anchor-propagation, notdef once implemented) when the release has FFTM, that is, when FontForge exported it. Do not pass them otherwise.

  Evidence: Two 149-style sweeps compared the patched converter plus 4 filters with unpatched 17ea899 (runs/reg-batch1-compare-all7.txt, runs/regnext-compare.txt). Table rows change only for Tuffy-Italic (26 -> 24), Cardo-Italic (10 -> 8) and Lohit-Tamil (8 -> 6). Rendering improves for MrDeHaviland (2 -> 0 glyphs), Thabit/Bold (1 -> 0) and Cardo-Italic (2 -> 0 words). It churns slightly in Tuffy-Regular (+2 words at 9-10 px; its v1.272 release has no FFTM) and Ultra-Regular (53 -> 52 glyphs, 321 -> 323 words; its release has a different point structure).
  Upstream: no
- **sfd-batch5/tools/table_gate.py**: Accept PfEd (FontForge's private table: lookup, subtable and anchor names) the way FFTM is accepted, and accept head.font_direction_hint (deprecated; FontForge writes 0 for mixed-direction fonts).

  Evidence: All four Thabit styles go from 2 rows to 0 (runs/p3/gate-ff-private). Cardo-Bold and Cardo-Italic have the same dirhint row.
  Upstream: no (workspace gate)
- **tools/baseline.sh, tools/land.py, tools/verify_landed.py**: Gate, or at least report, diffenator3's rendering diff (locations[].glyphs and words). table_gate.py delegates glyf/loca to 'the rendering diff', but none of these tools runs one.

  Evidence: Lohit-Bengali is table-CLEAN while 284 Bengali words render differently (marks unpositioned). Many batch-1 CLEAN styles also carry rendering diffs (runs/reg-batch1-compare-all7.txt, e.g. Miama 34 glyphs, Kristi 7).
  Upstream: no
- **tools/sfd_edit.py**: Add the ops mergefea, mergepsfont, obliqize, pastepsglyphs and appendcopyright, following FontForge 2008 (eb711fd7) as probes/ff_build_ops.py does. For exact Latin points, mergepsfont needs a port of splineorder2.c SplineSetsTTFApprox in place of cu2qu.

  Evidence: Thabit goes from 465 rows to 2 in each of the four styles (runs/p3). The Arabic is exact, and the Latin differs from the release by up to 0.2% in area.
  Upstream: no
- **babelfont-rs (SFD reader, mark lookups)**: Write FontForge's anchor-based mark lookups explicitly (per SFD lookup: its feature, script, anchor classes and bases) instead of leaving them to fontc's mark writer, at least when a feature mixes them with contextual lookups. A cheaper partial fix is an insertion marker in the declared feature.

  Evidence: Lohit-Bengali has 284 words differing. The marker brings that to 117 (runs/r4-lohit-bengali-marker): fontc then attaches to only 37-50 of the release's 240 bases and generates no blwm.
  Upstream: babelfont-rs: new PR (design discussion with Simon)

## Families that land once these are in

- lohittamil: CLEAN, 0 glyph and 0 word rendering diffs, once re-paired to 361b23b and the spacing-combining babelfont change is merged upstream (runs/r5-lohit-final)
- thabit (all 4 styles): 0 table rows once the new sfd_edit ops, the babelfont changes (lookupflag, baselig, rint, implied-oncurves, truncate-anchors, no-anchor-propagation, notdef), land.py's weight workaround and the PfEd/dirhint gate change are in. It still needs decisions D2-D5 and keeps the Latin cu2qu residue (<=46 px per glyph) until SplineSetsTTFApprox is ported.
- NOT lohitbengali: it lands table-CLEAN with the re-pairing alone, but 284 Bengali words render differently until the mark-lookup change exists

## Decisions for Felipe

- D1 Lohit: re-pair both styles to their provenance commits and correct google/fonts METADATA (a403c9b is the lohit-gujarati-2.92.1 tag) to 0df83ad for Bengali and 361b23b for Tamil. Also decide where they land: pravins/lohit is a live 13-family upstream, and land.py would branch 'modernize-sfd-to-glyphs' off 2011/2012 commits there, twice (both repos point at the same upstream).
- D2 Thabit: accept the 2010 hg .sfd as the base. The 2008-08-09 source state the 0.02 release was built from is not archived. The drawing is verified identical (0 Arabic rendering diffs in the uprights), but the names drifted. Should FamilyName 'Thabit' be restored as a documented edit whose value comes from the release's name table and METADATA?
- D3 Thabit: accept adding X.Org font-ibm-type1's IBM Courier AFMs (88a51da) as an input the hg tree lacks. They are needed for the release's latin f-ligature lookup.
- D4 Thabit: accept the build-script steps as documented .sfd edits (new sfd_edit ops) and the obliques as generated sources committed to the repository (where: src/ or a sources/generated/ convention).
- D5 Thabit Latin: port FontForge 2008's SplineSetsTTFApprox for exact Latin points, or accept the cu2qu stand-in (area within 0.2%, up to 46 px per glyph, Latin words up to 108 px).
- D6 Gate: accept PfEd and head.font_direction_hint (this also affects Cardo). Accept the obliques' release-stale lsb/bbox (FontForge 2008 truncated lsb, curve-extrema bbox) as not reproducible.
- D7 Gate: add a rendering gate to baseline.sh/land.py/verify_landed.py. Lohit-Bengali passes the table gate with 284 Bengali words differing. Landed families should be re-checked.
- D8 Yellowtail: take it out of the SFD programme. Options: (a) a babelfont Type 1 reader, landing from the PFB that is misnamed .sfd (the faithful outlines); (b) the VFB path, which is not faithful: Dave's 2011 simplification is not reproducible, and it gives 19 rows and 121 glyph diffs; (c) backlog.
- D9 Cardo-Italic: the spacing-combining fix closes 4 hmtx rows but opens 2 GDEF rows (fontc's kern writer puts the spacing marks in a mark filtering set). Hand this to Cardo's unit before the fix is upstreamed.

## Unresolved

- Lohit-Bengali mark positioning: babelfont needs to emit FontForge's anchor mark lookups explicitly. It is not prototyped; the insertion marker only gets 284 -> 117 words.
- Thabit Latin outlines: FontForge 2008 splineorder2.c SplineSetsTTFApprox is not ported. This leaves 60-83 Latin glyph diffs (up to 46 px) and 121-140 Latin/Greek words per style.
- Thabit's 0.02 build script (helper.py) is not archived. The reconstruction follows its successor build.py and matches the release structurally. Only the version and naming steps are uncertain: the release's name ID 5 is '0.01', while build.py sets 0.3.
- Thabit name table (not gated): the style name comes out 'Medium' because TTFWeight is 500, while FontForge used Weight: Regular. Name IDs 8/9/18 and the Arabic name 1 are not restored.
- --fontforge-notdef is still only an emulation, as it was for Tuffy.
- SetSubcategory can still overwrite 'Spacing Combining' on marks that carry underscore anchors. Nothing here exercises it.
- Cardo-Italic's kern mark-filtering-set rows opened by the spacing-combining fix.
- The obliques' release-stale lsb/bbox rendering (1 and 15 Arabic glyphs) cannot be reproduced from a source.
- Yellowtail has no convertible source in this programme: babelfont cannot read Type 1.
- The FontForge-exporter filters and all babelfont changes are prototypes on a scratch worktree of 17ea899 (/home/fsanches/compartilhado/sfd-reland-scratch/provenance/bf-spacing-mark, registered in babelfont-rs's worktree list). None is upstream, so nothing may land citing them. They have had no cargo fmt, clippy or tests.
- Session note: I ran 'git fetch -q upstream' once in the shared /home/fsanches/compartilhado/babelfont-rs (refs only). MrsSheppards failed once with ENOSPC because the /tmp tmpfs was 93% full, not mine; the rerun was CLEAN.
- Scratch is disposable: downloads can be re-fetched from the URLs and hashes in runs/thabit_release_inputs.txt, the patches are in probes/, and the builds are under sfd-reland-scratch/provenance, about 2.3 GB including target-bf. Nothing is committed, as instructed.

## Rerun

    cd /home/fsanches/compartilhado/sfd-reland && for s in Lohit-Bengali Lohit-Tamil Thabit Thabit-Bold; do FAMILIES=$PWD/families-next.tsv BF=/home/fsanches/compartilhado/babelfont-rs-worktrees/integration-ff-prs/target-heights/release/babelfont OUT=$PWD/investigations/next-provenance/runs/r0-baseline TAG=provenance-r0 SCRATCH=/home/fsanches/compartilhado/sfd-reland-scratch/provenance bash tools/baseline.sh $s; done
    P=/home/fsanches/compartilhado/sfd-reland/investigations/next-provenance; /home/fsanches/compartilhado/gftools/venv/bin/python3 $P/probes/fftm_source_commit.py <release.ttf> <archive repo.git> <path.sfd>   (see its docstring for the 4 invocations)
    cd /home/fsanches/compartilhado/sfd-reland && FAMILIES=$PWD/investigations/next-provenance/runs/r1-lohit-provenance/families.tsv BF=<scratch>/target-bf/release/babelfont EXTRA_FLAGS='--fontforge-implied-oncurves --fontforge-rint-coordinates --fontforge-truncate-anchors --fontforge-no-anchor-propagation' OUT=$PWD/investigations/next-provenance/runs/r5-lohit-final TAG=provenance-r5 SCRATCH=/home/fsanches/compartilhado/sfd-reland-scratch/provenance bash tools/baseline.sh Lohit-Tamil   (and Lohit-Bengali)
    Build the prototype: git -C /home/fsanches/compartilhado/babelfont-rs worktree add --detach <scratch>/bf 17ea899 && git -C <scratch>/bf apply probes/babelfont-prototype-all7.patch && sudo -n /usr/local/sbin/drop-caches; CARGO_BUILD_JOBS=3 CARGO_TARGET_DIR=<scratch>/target-bf cargo build --release -p babelfont --features cli
    cd /home/fsanches/compartilhado/sfd-reland/investigations/next-provenance && bash probes/thabit_pipeline.sh p3 '--fontforge-implied-oncurves --fontforge-rint-coordinates --fontforge-truncate-anchors --fontforge-no-anchor-propagation'   (writes runs/p3/SUMMARY.txt)
    for st in Thabit Thabit-Bold Thabit-Oblique Thabit-BoldOblique; do d=<scratch>/baseline/$st-p3-workarounds; python3 probes/table_gate_ff_private.py $d/d3.json --fonts /home/fsanches/compartilhado/google/fonts/ofl/thabit/$st.ttf $d/fonts/ttf/*.ttf; done
    python3 probes/stale_lsb.py /home/fsanches/compartilhado/google/fonts/ofl/thabit/Thabit-BoldOblique.ttf <scratch>/baseline/Thabit-BoldOblique-p3-workarounds/d3.json
    bash probes/mark_feature_marker.sh <scratch>/baseline/Lohit-Bengali-provenance-r2 Lohit-Bengali abvm /home/fsanches/compartilhado/google/fonts/ofl/lohitbengali/Lohit-Bengali.ttf runs/r4-lohit-bengali-marker
    python3 probes/yellowtail_lineage.py; python3 probes/yellowtail_pfb_geometry.py; bash probes/yellowtail_vfb_measure.sh runs/y1-yellowtail-vfb
    cd /home/fsanches/compartilhado/sfd-reland && FAMILIES=$PWD/families.tsv (or families-next.tsv) BF=<unpatched or prototype> [EXTRA_FLAGS=<4 filters>] OUT=<runs dir> TAG=<tag> SCRATCH=<scratch>/reg bash tools/baseline.sh --all; python3 investigations/next-provenance/probes/sweep_summary.py <outA> <scratchA> <tagA> <outB> <scratchB> <tagB>   (results: runs/reg-batch1-compare-all7.txt, runs/regnext-compare.txt)
