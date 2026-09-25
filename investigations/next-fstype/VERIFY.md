# next-fstype -- adversarial verification

**Model**: Claude Opus 5.5. Written from the verifier's structured result.

Reproduced: True

I reproduced every run independently, without reading the agent's candidate generator or pairing table. Inputs: my own families-verify.tsv (families-next.tsv's 10 rows plus 2 ExtraLight rows I derived myself) and my own candidates made with the tools/sfd_edit.py CLI (probes/make_verify_inputs.sh, runs/candidates.log). My c-fstype, c-elfull and c-version .sfd files came out byte-identical to the agent's cand-* files. Tools: converter babelfont integration-ff-prs 17ea899 (BUILT_FROM 17ea8995); builder3 e851b8b with fontc 1.0.0; gate 2f43693; google/fonts working copy at b5efa9c32 on main, where all 12 shipped blobs equal b5efa9c32 and 93550bd32.

Harness results (tools/baseline.sh, one build per style; runs under /home/fsanches/compartilhado/sfd-reland/investigations/next-fstype-verify/runs):
- v0 fidelity-only: 21 rows (fs_type x12, us_weight_class x9). The gate text is identical to baseline-next/ for all 10 paired styles, not just the 3 the agent compared, and identical to the agent's r0 for all 12.
- v1 (tools/workarounds.py applied as land.py applies it): 14 rows (fs_type x12, ExtraLight us_weight_class [275,200] x2).
- v2 (+FSType 0): 10 CLEAN; the 2 ExtraLight weight rows remain.
- v3a (+TTFWeight 275 only, no rename): both ExtraLight styles CLEAN 0.
- v3c (+full rename): CLEAN, and name IDs 1/4/6/17 equal the release's.
- v4 (+version edits): 11/11 CLEAN. fontRevision and name ID 3 equal the release's; name ID 5 differs only by ';fontc 1.0.0'.

One-config family build, with built files named by land.built_name(): 11/11 gate 0. The Titillium .sfd for style X is src/TitilliumWeb-X-TTF.sfd; the ExtraLight pair is src/TitilliumWeb-Thin-TTF.sfd -> ofl/titilliumweb/TitilliumWeb-ExtraLight.ttf, and ThinItalic -> ExtraLightItalic. Every source is at googlefontdirectory-hg 52f780bc9, which is the hg tip, so no later hg edit exists.

History checks, all confirmed:
- google/fonts 90abd17b4 binaries are byte-identical to the hg 52f780bc9 blobs.
- 8ccda7bf7 changed only the raw OS/2 and head tables of Wallpoet (fsType 4->0).
- 93550bd32 changed only OS/2, head and name in the Titillium files.
- FFTM.sourceModified equals the .sfd ModificationTime.
- FontForge tottf.c v20110222:3315-3317 and v20120731-b:3403-3405 (fsType), and 2760/2850 (head.revision = sfntRevision), fetched and matching.
- hg METADATA.json independently confirms the pairing: filename TitilliumWeb-ExtraLight.ttf, postScriptName TitilliumWeb-Thin.

Beyond the gate:
- diffenator3 reports no glyph or word difference and the cmap is exact (runs/d3_cmap_summary.txt).
- diffenator3's kern comparison gives up ('There are 2332 changes, check manually!'), and the gate's arbitrate_gpos accepts the GPOS rows without shaping anything. So I shaped every PairPos pair of all 11 Titillium styles through HarfBuzz (8,820 to 115,632 pairs each), with default features and with cpsp on: 0 pairs position differently (runs/kern_pairs_shape.txt).
- fontspector A/B (1.6.0) is identical to the agent's tables: 0 checks worse.

Location note: I used investigations/next-fstype-verify/{probes,runs} and scratch /home/fsanches/compartilhado/sfd-reland-scratch/fstype-verify (576 MB, all regenerable from the probes). The task also mentioned investigations/next-fstype/verify/, but that path was not used. Nothing was committed, as instructed. Under Felipe's rule, the probes/ and runs/ directories are what should be committed with this unit. tools/sfd_edit.py shows as modified in git status; I did not make that change (it is another unit's addprivate op).

## Verdict

The investigation's core is correct and every number reproduced independently: the fsType release edits (93550bd32, 8ccda7bf7), the fontc weight-class gap, the ExtraLight <- Thin pairing, TTFWeight 275, the version option, and 11/11 plus 1/1 CLEAN, including the one-config family build. All six proposed .sfd edits hold; the values and origins are right and my candidates are byte-identical to the agent's.

Needs correction:
- The ExtraLight rename closes no gate row, and within it only FontName and LangName ID 3 affect this converter's build.
- The babelfont PS-name PR text: affected-landing count (16, not 10), environmental test failures that can be proven statically, integration tests not run, and name ID 4 is fixable through a Name Table Entry.
- The ExtraLight UNPAIRED row is a pairing-tool gap, not 'provenance'.
- Rule 4 should make its corroboration check mandatory.

Missed:
- babelfont's Glyphs start-node convention bug, which rotates every contour's start point. It explains the 'unresolved' Wallpoet fontspector change: 61 vs 112 colinear hits; the PASS is an artefact of the >100 early return.
- The oslash implied-point drop behind 3442 vs 3441.
- Wallpoet's dropped source-stated TrueType hinting, which should be disclosed.
- A version_bump misreading.

Kerning, which the gate never shapes for GPOS-shipping styles, is now verified: all pairs of all 11 Titillium styles position identically. Neither landing is blocked; both remain *-UNPUBLISHED-CONVERTER until babelfont #91/#92/#93 merge.

## Per edit

- [keep] Set fsType to 0, installable embedding -- Titillium, all 11 styles. Verified: 93550bd32 changed fsType 8->0 in every binary; all 11 .sfd state FSType: 8; hg 52f780bc9 is the tip, so no later source edit exists; FontForge's exporter writes the stated value (tottf.c v20120731-b:3403-3405). v2 closes every fs_type row. The body names the commit and states the value came from the release.
- [keep] Rename Thin to ExtraLight, as Google Fonts ships it -- The values match 93550bd32's name table and METADATA.pb, and the body says they were copied from the release. Two corrections to the evidence. (1) The rename closes no gate row: v3a (TTFWeight 275, no rename) is already CLEAN 0; the rename matters only for name IDs 1/3/4/6/17, which the gate does not compare. (2) With this converter only FontName and LangName ID 3 change the build. babelfont takes the master style from FontName's '-' suffix (fontforge.rs ~950). FullName is never written to the .glyphs. LangName ID 17 is written as the Glyphs styleNames property, which fontc 1.0.0 does not map. v3b, which changed only LangName ID 17, still built 'Titillium Web Thin' / 'TitilliumWeb-Thin'. Keeping all the fields is still right, because the source then states the release's names.
- [keep] Rename Thin Italic to ExtraLight Italic, as Google Fonts ships it -- Same findings as the upright rename; v3c confirms IDs 1/2/4/6/17 equal the release's. The new LangName ID 2 'ExtraLight Italic' matches the release's Mac record; the Windows record is 'Italic', which fontc derives.
- [keep] Set usWeightClass to 275, as Google Fonts ships it -- Verified: 93550bd32 raised usWeightClass 200->275 in both ExtraLight binaries. The .sfd, the original export and METADATA.pb all say 200. v3a shows this edit alone closes the [275,200] row once land.py's weight workaround carries TTFWeight into the FEA.
- [keep] Set fsType to 0, installable embedding -- Wallpoet. Verified: 8ccda7bf7 changed only the OS/2 table (fsType 4->0) and the head checksum. The .sfd states 4, and the hg tip has no later edit. The plan is identical to plans/russoone.json. v2: CLEAN 0.
- [keep] Set the version to 1.002, as Google Fonts ships it -- Optional, and correctly left to Felipe (the tuffy precedent is also optional). v4: 11/11 CLEAN; head.fontRevision is 1.002 (0x00010083), name ID 3 is exact, name ID 5 differs only by ';fontc 1.0.0'. The sfntRevision part is inert with this converter (fontforge.rs:844 ignores the key), as the agent says. It needs the proposed setname op or whole-line LangName setfields. One evidence claim is wrong: fontspector googlefonts/version_bump PASSes on the 1.001 build and FAILs on the shipped fonts only because 1.0019989 equals the served version. The check does not flag the downgrade; only the head/name comparison shows it.

## Per tool change

- [revise] tools/pair_next.py rule 4 (history-based pairing) -- The result is correct: it pairs only the 2 Titillium ExtraLight rows and leaves Thabit x2 and Yellowtail unpaired, and hg METADATA.json independently confirms the pairs. But rule 4 treats the corroboration as optional and relies on `git log --follow` plus name ID 6 alone. That is the kind of weak evidence that has produced mis-pairs in this programme before. Make a check mandatory: either FFTM.sourceModified equals the .sfd ModificationTime, or the glyph-bearing tables are unchanged between the historic and current revisions (both hold here). Log which one passed.
- [revise] babelfont-rs glyphs3.rs PostScript-name mapping -- The defect is real. At 17ea899:569-575 and upstream main 91bf8bb, names.postscript_name is written as postscriptFullName and name ID 20 as postscriptFontName. fontc's glyphs2fontir try_name_id reads postscriptFontName as name ID 6 and has postscriptFullName commented out. My own key-swap test on the Wallpoet .glyphs gives ID 6 'Wallpoet' (runs/psname_key_swap.txt), so the direction is right. Details to fix before filing: (a) The affected-landing count is wrong. UnifrakturMaguntia has no landed.tsv row. There are 9 CLEAN landings (Nova x7, SixCaps, Smythe) plus 7 CLEAN-UNPUBLISHED-CONVERTER landings (LovedbytheKing, OvertheRainbow, Ruluko-Regular, SwankyandMooMoo, TheGirlNextDoor, TitanOne-Regular, Trochut-Regular), 16 in all. I checked their baseline builds: all lose IDs 6 and 4. (b) The 11 failing lib tests are provably environmental. .github/workflows/rust.yml:31 clones noto-cjk-varco separately, and the failures are 'Failed to read designspace.json: No such file'. babelfont/tests/integration.rs was not run at all. (c) Name ID 4 can be fixed from the converter side. glyphs-reader 1.0.0 parses a font-level 'Name Table Entry' custom parameter and source.rs applies it after building the names; adding '4; Wallpoet' built ID 4 'Wallpoet'. (d) Untested: once fontc honours a font-level postscriptFontName, a multi-instance source would carry one name ID 6 at font level.
- [keep] babelfont-rs fontforge.rs: head.fontRevision from sfntRevision -- Checked against the fetched tottf.c: v20110222:2760 and v20120731-b:2850 set head->revision = sf->sfntRevision, falling back to the Version string only when it is unset. The original export has 1.000, our build 1.001. sfntRevision is in the ignore list at fontforge.rs:844 on both 17ea899 and upstream main. A fidelity rule a maintainer could merge; it moves no gate row, so low priority, as the agent says.
- [keep] fontc glyphs2fontir: single-master weightClass -- `git grep us_weight_class` on fontc origin/main 66637808 finds no setter in glyphs2fontir; fontbe/src/os2.rs:546 falls back to the wght axis or 400. The existing workaround closes the 9 weight rows (v0 -> v1). The issue draft already exists.
- [keep] tools/sfd_edit.py new op setname -- The prototype (make_candidates.py setname) refuses non-ASCII, '+' and '"' values and any content outside the quoted strings, and reports the before value. My candidates, built with whole-line `setfield LangName`, are byte-identical to its output. Only the optional version edit needs it.

## Objections

- The UNPAIRED row for TitilliumWeb-ExtraLight / -ExtraLightItalic is classified 'provenance'. The binary's provenance is certain: exported from src/TitilliumWeb-Thin(Italic)-TTF.sfd, with FFTM.sourceModified equal to its ModificationTime, byte-identical to hg, and confirmed by hg METADATA.json. The row is a gap in pair_next.py's rules, closed by the rule-4 tool change. In the precedent (PatrickHand), 'provenance' meant the release was not exported from the .sfd, which is not the case here.
- Wallpoet name ID 4 is listed as unresolved because 'no converter-side fix restores Wallpoet'. That is false. fontc 1.0.0 applies a font-level 'Name Table Entry' custom parameter after building the names, and the '4; Wallpoet' variant built ID 4 'Wallpoet' (runs/psname_key_swap.txt). Like ID 6, it is converter-fidelity, not only compiler-derived.
- Minor: the Titillium version row is a 'decision', which matches the tuffy precedent. But the unit's stated rule says any difference the release has and the source lacks must be a tool fix or a documented edit. Felipe should know the optional framing departs from that wording.

## Missed

- Contour start point, a converter-fidelity issue in babelfont that the agent did not report. babelfont's model draws closed paths from nodes[0] (shape.rs to_kurbo). Its glyphs3 path conversion (shape.rs:696-735) copies node lists without rotating them. But Glyphs, glyphsLib and fontc treat the LAST node of a closed path as its start (glyphs2fontir toir.rs: 'the starting node of a closed contour is always stored at the end'). So every contour starts one node later than in FontForge's export: Wallpoet 394/394 rotated by 1; Titillium by 1 or 2 in every style (runs/start_point_rotation.txt). Traced on H in TitilliumWeb-Regular: the .sfd starts at (514,0), the .glyphs lists (514,0) first, and the build starts at (514,313). Rendering is unaffected. This explains the agent's unexplained Wallpoet fontspector change (outline_colinear_vectors / outline_short_segments WARN->PASS). The release has 49 FontForge closing duplicates (first point == last), which are not segments. The rotation moves them into the middle of the contour as zero-length segments. My emulation of colinear_vectors.rs gives 61 hits on the release (fontspector: WARN, 61 listed) and 112 on the build; above 100 the check returns PASS early. The 'better' status is therefore an artefact. Fix: rotate closed paths on write and read in the glyphs3 conversion; the same file as the PS-name PR, but a separate change.
- The 3442 vs 3441 point count the agent left open: the only glyph that differs beyond the rotation is oslash. The build omits the on-curve (653,380), which is exactly the midpoint of its off-curve neighbours (645,384) and (661,376). The outline is identical (runs/point_counts_wallpoet.txt).
- Wallpoet's release is hinted with the .sfd's own TrueType instructions: TtTable prep and fpgm, ShortTable cvt, gasp, and 178 glyph programs (180 TtInstrs/TtTable lines in Wallpoet-Regular-TTF.sfd). The build is unhinted. The gate accepts the prep/fpgm/cvt/gasp/glyf differences, and Puritan's FINDINGS notes the converter ignores instructions, but the unit's result never mentions it. Rendering on hinting rasterizers at small sizes differs, so it should be disclosed in Wallpoet's future_work / PR body. Titillium ships no glyph programs, so it is not affected.
- The PS-name loss affects 16 landings, not 10, and UnifrakturMaguntia-Book is not landed: 9 CLEAN plus 7 CLEAN-UNPUBLISHED-CONVERTER (LovedbytheKing, OvertheRainbow, Ruluko-Regular, SwankyandMooMoo, TheGirlNextDoor, TitanOne-Regular, Trochut-Regular). I checked their baseline-next builds: ID 6 gains '-Regular' and ID 4 gains ' Regular'.
- 93550bd32 changed more than the unit's rows. It fixed name ID 4 spacing in all 11 styles ('Titillium WebBlack' -> 'Titillium Web Black'), restructured RIBBI names in 6 styles (IDs 1/2/16/17), removed ID 18 from Regular, and changed the fsSelection/macStyle bold bits of Black, SemiBold and SemiBoldItalic and the REGULAR bit of Light and ExtraLight. The build matches all of this only because fontc derives names and flags from the style, not because the sources say so (they still say 'Titillium WebBlack'). If the converter starts carrying FullName (for example the Name Table Entry route to fix Wallpoet's ID 4), 11 Titillium ID 4 rows appear and each needs a FullName edit citing 93550bd32. The ExtraLight-only FullName edit is also inconsistent with leaving the other 9 FullNames unedited.
- fontspector version_bump was misread (see the version edit verdict): it PASSes 1.001 and does not show the downgrade.
- The claim that there is no other source should cite upstream_info.md's ecm4u/Titillium. I checked it: it is the separate 'Titillium' family (Titillium-*.sfd, a mirror created in 2020), not Titillium Web, so the conclusion stands.
