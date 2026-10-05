# next-heights -- investigation findings

**Model**: Claude Opus 5.5 (investigating agent, adversarial verifier, and the
conclusion below). Written from the agents' structured results (`results.json`).

## Conclusion

All 16 styles close. Most of these -TTF.sfd files were re-imported from the release TTF
(ttf2sfd.py) and lost the CFF BlueValues of src/<X>.otf, the file FontForge exported the
release from (its head.created equals the release's FFTM sourceCreated); SFStandardHeight
snapped to those zones. One documented `addprivate BlueValues` edit per style restores
them (13 styles), and a #91 follow-up (a glyph is found by any of its codepoints, as
SFFindGID does) closes KottaOne, Macondo and Rosarivo-Italic. Ledger also needs the
nbsp-width edit google/fonts made. 13 families land CLEAN with these.

## Investigator's report

Paired harness runs (tools/baseline.sh, families-next.tsv, one build per style; SCRATCH
under sfd-reland-scratch/heights). The before set with BF integration-ff-prs 17ea899
reproduces baseline-next gate for gate on all 16 styles. altuni (the #91 lookup fix
alone) closes KottaOne, Macondo and Rosarivo-Italic. blues (addprivate BlueValues for 13
styles and nbspwidth for Ledger, on 17ea899) closes every height row and the nbsp row of
the 13 edited styles. final (fix plus edits) leaves only the 5 us_weight_class rows, and
land.py's own workaround (tools/workarounds.py, TTFWeight as FEA) closes those: all 16
styles CLEAN. No gate line other than the targeted rows changed in any set
(nothing_else_opened), and the .glyphs differ only in the x/cap metric values and
Ledger's nbsp width. Root-cause evidence: the -TTF.sfd of all 20 styles is a re-import
of the release TTF, shown by FFTM source dates = sfd times, identical prep/gasp, and
identical advance and point bbox for every non-composite glyph (runs/provenance.txt).
The FFTM-selected vintage, applied to the -TTF.sfd outlines with the .otf's CFF
BlueValues, reproduces every released sxHeight/sCapHeight of all 20 styles; without the
BlueValues, 13 differ (runs/hypotheses.txt). 15 of the 16 releases are byte-identical to
the 2012 base-tree binaries; Ledger differs only by google/fonts 0436d99c0/f8265bddf
(runs/release_history.txt).

Rows before: 30 blocking rows across 16 styles (24 OS/2 x/cap, 5 us_weight_class, 1 hmtx.uni00A0); runs/before/ matches baseline-next/

Rows after: altuni only: 27. blues only: 8 (3 AltUni x-heights + 5 weight class). final: 5 (weight class only). final + land.py workaround: 0. All 16 styles CLEAN; the 4 CLEAN siblings stay CLEAN.

Confidence: High. Two causes account for all 24 height rows, and each was verified by exact reproduction. (1) Thirteen styles lost the BlueValues their releases were snapped to. The evidence is the documented 2012 production recipe (HOWTOGEN.txt and the nonhinting scripts), a glyph-by-glyph proof that each -TTF.sfd is a re-import of the release TTF, the FontForge C at the release's own FFTM builds, and harness runs that close every row and change nothing else. (2) A fidelity gap in #91's glyph lookup: FontForge's SFFindGID matches AltUni, and 'mu' is U+00B5 plus AltUni U+03BC. It is verified with exact divisor arithmetic, a harness run and a 149-style regression. The Ledger nbsp row is the google/fonts 0436d99c0 edit. The weight-class rows are the known fontc gap, closed by land.py's existing workaround.

## Rows

| style | row | class | cause |
|---|---|---|---|
| KottaOne-Regular | OS/2.sx_height [76, 81] | converter-fidelity | babelfont #91 (fontforge_standard_height.rs, glyphs_by_primary_codepoint) finds a glyph by its FIRST codepoint only. FontForge's SFGetChar -> SFFindGID -> SCUniMatch (fvfonts.c, identical at b69c9652 = FFTM 20110222, at 5a11aa4c and at master) matches the lowest gid whose unicodeenc OR any AltUni is the codepoint. Glyph 'mu' (Encoding 181, AltUni2 0003bc) is therefore the 19th x-height glyph for U+03BC. The release FFTM is 20110222, so the glyph-count mean applies: the distinct round tops are 480, 485 and 495 (sum 1460). FontForge divides by 19 glyphs: 76.84, so 76. babelfont divides by 18: 81.1, so 81. |
| Macondo-Regular | OS/2.sx_height [24, 25] | converter-fidelity | Same AltUni lookup gap as KottaOne. 'mu' (Encoding 181, AltUni2 0003bc) is missed. All 19 x-height tops are round at 456, and the FFTM is 20110222 (glyph-count mean). FontForge gives 456/19 = 24.0, so 24; babelfont gives 456/18 = 25.3, so 25. |
| Rosarivo-Italic | OS/2.sx_height [217, 229] | converter-fidelity | Same AltUni lookup gap. 'mu' (Encoding 181, AltUni2 0003bc) has a pointy top at 509, a height it shares with c, e and o, so only the divisor changes. The distinct tops 500, 509, 511, 513, 516, 521, 528 and 540 sum to 4138, and the FFTM is 20110222. FontForge gives 4138/19 = 217.8, so 217; babelfont gives 4138/18 = 229.9, so 229. |
| Ledger-Regular | OS/2.sx_height [487, 485] | provenance | The release was exported by FontForge 20110222 (FFTM) from the font it had opened from src/Ledger-Regular.otf. The process is tools/generate/HOWTOGEN.txt with tools/nonhinting/setquadraticaddextremasimplify-fontforge.py in googlefontdirectory-hg 52f780bc. SFStandardHeight snapped the rule value to the nearest BlueValues zone bottom within (ascent+descent)/100 = 10 (splinefont.c). The zones were those of the .otf's CFF Private [-21 0 487 495 750 768], which FontForge's reader stores in sf->private (parsettf.c cffprivatefillup). The paired -TTF.sfd was made later by ttf2sfd.py from the release TTF, and a TTF cannot carry a private dictionary. On the outlines, the rule gives a flat 485, which snaps to 487. The 2012 binary already had 487; the 2020 edits did not touch OS/2. |
| Ledger-Regular | hmtx.uni00A0 {"width": [281, 0]} | source-edit-from-release | google/fonts 0436d99c0 (2020-06-23, Measure + Fit, 'ledger: fixed nbsp width (#2353)') changed the binary's U+00A0 advance from 0 to 281, which is the space's width, and also changed head and name (1.001 -> 1.002). f8265bddf ('v1.003 added (#2514)') changed only head and name. The .sfd states uni00A0 Width 0 and space Width 281. |
| LilitaOne-Regular | OS/2.sx_height [506, 500] | provenance | Lost BlueValues, the same mechanism as Ledger (FFTM 20110222, 2011 rule). The rule gives 500.0, which snaps to the zone bottom 506 of src/LilitaOne-Regular.otf [-10 0 506 510 704 709]. |
| LilitaOne-Regular | OS/2.s_cap_height [704, 700] | provenance | Lost BlueValues: the rule gives 700.0, which snaps to the zone bottom 704. |
| Lustria-Regular | OS/2.sx_height [504, 511] | provenance | Lost BlueValues (FFTM 20110222). The rule gives 511.0, which snaps to the zone BOTTOM 504 of src/Lustria-Regular.otf [-11 0 504 511 704 711], at a distance of 7. |
| Lustria-Regular | OS/2.s_cap_height [704, 700] | provenance | Lost BlueValues: the rule gives 700.0, which snaps to 704. |
| Magra-Bold | OS/2.sx_height [525, 533] | provenance | Lost BlueValues (FFTM 20110222). The rule gives 533.0, which snaps to the zone bottom 525 of src/Magra-Bold.otf [-12 0 525 537 700 712 750 760]. |
| Magra-Bold | OS/2.s_cap_height [700, 708] | provenance | Lost BlueValues: the rule gives 708.0, which snaps to 700. |
| Magra-Bold | OS/2.us_weight_class [600, 400] | compiler-gap | fontc 1.0.0 ignores a static single-master Glyphs source's weightClass (issues/fontc-static-weight-class.md). The .sfd states TTFWeight: 600. land.py closes the row with tools/workarounds.py, which carries the value as FEA. |
| MergeOne-Regular | OS/2.sx_height [493, 492] | provenance | Lost BlueValues. The export was by FontForge 20120906 (FFTM), so the distinct-tops mean applies. The rule gives 492.0, which snaps to the zone bottom 493 of src/MergeOne-Regular.otf [-8 0 493 502 679 687]. |
| OleoScript-Bold | OS/2.sx_height [443, 436] | provenance | Lost BlueValues (FFTM 20120906). The rule gives 436.5, which snaps to 443 of src/OleoScript-Bold.otf [-12 0 443 443 710 710]. |
| OleoScript-Bold | OS/2.s_cap_height [710, 708] | provenance | Lost BlueValues: the rule gives 708.75, which snaps to 710. Only the 2012 rule plus the blues reproduces it, which is consistent with the FFTM. |
| OleoScript-Bold | OS/2.us_weight_class [700, 400] | compiler-gap | fontc 1.0.0 static weightClass gap. The .sfd states TTFWeight: 700, and tools/workarounds.py closes the row at landing. |
| OleoScript-Regular | OS/2.sx_height [443, 442] | provenance | Lost BlueValues (FFTM 20120906). The rule gives 442.5, which snaps to 443 of [-12 0 443 450 710 710]. |
| OleoScript-Regular | OS/2.s_cap_height [710, 709] | provenance | Lost BlueValues: the rule gives 709.0, which snaps to 710. |
| OleoScriptSwashCaps-Bold | OS/2.sx_height [443, 436] | provenance | Lost BlueValues (FFTM 20120906). The rule gives 436.5, which snaps to 443 of [-13 0 443 443 747 747]. |
| OleoScriptSwashCaps-Bold | OS/2.s_cap_height [747, 750] | provenance | Lost BlueValues: the rule gives 750.2, which snaps to 747. The .otf's own OS/2 says 710, so 747 does not come from copying the .otf's OS/2. |
| OleoScriptSwashCaps-Bold | OS/2.us_weight_class [700, 400] | compiler-gap | fontc 1.0.0 static weightClass gap. The .sfd states TTFWeight: 700. |
| OleoScriptSwashCaps-Regular | OS/2.sx_height [443, 442] | provenance | Lost BlueValues (FFTM 20120906). The rule gives 442.5, which snaps to 443 of [-12 0 443 450 747 747]. |
| Rambla-Bold | OS/2.sx_height [517, 513] | provenance | Lost BlueValues (FFTM 20120906). The rule gives 513.0, which snaps to 517 of src/Rambla-Bold.otf [-13 0 517 524 669 680]. |
| Rambla-Bold | OS/2.s_cap_height [669, 668] | provenance | Lost BlueValues: the rule gives 668.0, which snaps to 669. |
| Rambla-Bold | OS/2.us_weight_class [700, 400] | compiler-gap | fontc 1.0.0 static weightClass gap. The .sfd states TTFWeight: 700. |
| Rambla-BoldItalic | OS/2.sx_height [517, 513] | provenance | Lost BlueValues (FFTM 20120906). The rule gives 513.0, which snaps to 517 of src/Rambla-BoldItalic.otf [-13 0 517 524 669 680]. |
| Rambla-BoldItalic | OS/2.s_cap_height [669, 668] | provenance | Lost BlueValues: the rule gives 668.0, which snaps to 669. |
| Rambla-BoldItalic | OS/2.us_weight_class [700, 400] | compiler-gap | fontc 1.0.0 static weightClass gap. The .sfd states TTFWeight: 700. |
| Sail-Regular | OS/2.s_cap_height [666, 665] | provenance | Lost BlueValues (FFTM 20110222, 2011 rule). The rule gives a flat 665.0, which snaps to 666 of src/Sail-Regular.otf [0 0 389 389 666 666]. The x-height of 435 lies 46 from the nearest zone and is unaffected. |
| TextMeOne-Regular | OS/2.sx_height [502, 500] | provenance | Lost BlueValues (FFTM 20120906). The rule gives 500.0, which snaps to 502 of src/TextMeOne-Regular.otf [-1 0 502 502 700 706]. |

## Proposed .sfd edits

- **Restore the BlueValues the release was exported with** (Ledger-Regular) `addprivate BlueValues [-21 0 487 495 750 768]` -- verified: True; value from: CFF Private BlueValues of src/Ledger-Regular.otf in googlefontdirectory-hg 52f780bc. That is the file FontForge 20110222 opened and exported the release from, per HOWTOGEN.txt and setquadraticaddextremasimplify-fontforge.py. The value is written as FontForge's CFF reader stored it (parsettf.c realarray2str), printed by probes/otf_bluevalues.py. It is not read from the release.; the source stated: No BeginPrivate section, so no BlueValues. No OS2XHeight or OS2CapHeight.
- **Give the no-break space the space's width, 281** (Ledger-Regular) `nbspwidth ` -- verified: True; value from: The .sfd's own space Width 281. The change it reproduces is google/fonts 0436d99c0 (2020-06-23), which set hmtx uni00A0 from 0 to 281 (runs/ledger_release_history.txt).; the source stated: uni00A0 Width: 0; space Width: 281
- **Restore the BlueValues the release was exported with** (LilitaOne-Regular) `addprivate BlueValues [-10 0 506 510 704 709]` -- verified: True; value from: CFF Private BlueValues of src/LilitaOne-Regular.otf (googlefontdirectory-hg 52f780bc); exporter FontForge 20110222; the source stated: No BeginPrivate section; no stated heights
- **Restore the BlueValues the release was exported with** (Lustria-Regular) `addprivate BlueValues [-11 0 504 511 704 711]` -- verified: True; value from: CFF Private BlueValues of src/Lustria-Regular.otf (52f780bc); exporter FontForge 20110222; the source stated: No BeginPrivate section; no stated heights
- **Restore the BlueValues the release was exported with** (Magra-Bold) `addprivate BlueValues [-12 0 525 537 700 712 750 760]` -- verified: True; value from: CFF Private BlueValues of src/Magra-Bold.otf (52f780bc); exporter FontForge 20110222. Magra-Regular gets no edit: it is CLEAN.; the source stated: No BeginPrivate section; no stated heights
- **Restore the BlueValues the release was exported with** (MergeOne-Regular) `addprivate BlueValues [-8 0 493 502 679 687]` -- verified: True; value from: CFF Private BlueValues of src/MergeOne-Regular.otf (52f780bc); exporter FontForge 20120906; the source stated: No BeginPrivate section; no stated heights
- **Restore the BlueValues the release was exported with** (OleoScript-Bold) `addprivate BlueValues [-12 0 443 443 710 710]` -- verified: True; value from: CFF Private BlueValues of src/OleoScript-Bold.otf (52f780bc); exporter FontForge 20120906; the source stated: No BeginPrivate section; no stated heights
- **Restore the BlueValues the release was exported with** (OleoScript-Regular) `addprivate BlueValues [-12 0 443 450 710 710]` -- verified: True; value from: CFF Private BlueValues of src/OleoScript-Regular.otf (52f780bc); exporter FontForge 20120906; the source stated: No BeginPrivate section; no stated heights
- **Restore the BlueValues the release was exported with** (OleoScriptSwashCaps-Bold) `addprivate BlueValues [-13 0 443 443 747 747]` -- verified: True; value from: CFF Private BlueValues of src/OleoScriptSwashCaps-Bold.otf (52f780bc); exporter FontForge 20120906; the source stated: No BeginPrivate section; no stated heights
- **Restore the BlueValues the release was exported with** (OleoScriptSwashCaps-Regular) `addprivate BlueValues [-12 0 443 450 747 747]` -- verified: True; value from: CFF Private BlueValues of src/OleoScriptSwashCaps-Regular.otf (52f780bc); exporter FontForge 20120906; the source stated: No BeginPrivate section; no stated heights
- **Restore the BlueValues the releases were exported with** (Rambla-Bold, Rambla-BoldItalic) `addprivate BlueValues [-13 0 517 524 669 680]` -- verified: True; value from: CFF Private BlueValues of src/Rambla-Bold.otf and src/Rambla-BoldItalic.otf (52f780bc), identical in both; exporter FontForge 20120906. Rambla-Regular and Rambla-Italic get no edit: they are CLEAN.; the source stated: No BeginPrivate section; no stated heights
- **Restore the BlueValues the release was exported with** (Sail-Regular) `addprivate BlueValues [0 0 389 389 666 666]` -- verified: True; value from: CFF Private BlueValues of src/Sail-Regular.otf (52f780bc); exporter FontForge 20110222; the source stated: No BeginPrivate section; no stated heights
- **Restore the BlueValues the release was exported with** (TextMeOne-Regular) `addprivate BlueValues [-1 0 502 502 700 706]` -- verified: True; value from: CFF Private BlueValues of src/TextMeOne-Regular.otf (52f780bc); exporter FontForge 20120906; the source stated: No BeginPrivate section; no stated heights

## Proposed tool changes

- **babelfont-rs (follow-up commit on PR #91, branch pr-ff-os2-defaults @119f2be)**: In fontforge_standard_height.rs, look a glyph up by ANY of its codepoints, not just the first. Iterate glyphs in order and take the first glyph mapped to the codepoint, whether as its own codepoint or as an alternate (AltUni2). This is what FontForge's SFGetChar -> SFFindGID -> SCUniMatch does: a single pass over gids matching unicodeenc OR any altuni. The code is the same at b69c9652 (20110222), 5a11aa4c (20120906) and master. The change renames glyphs_by_primary_codepoint to glyphs_by_codepoint and adds the unit test test_a_glyph_is_found_by_an_alternate_codepoint.

  Evidence: Harness runs: KottaOne, Macondo and Rosarivo-Italic go from BLOCKING 1 to CLEAN 0 (runs/altuni/). No other gate line changes (runs/nothing_else_opened-before-altuni.txt). The .glyphs change only in x-height: 81->76, 25->24, 229->217. The four CLEAN siblings stay CLEAN with gates identical to baseline-next (runs/altuni-siblings-vs-baseline-next.txt). Conversion-only regression over all 149 styles of both batches (runs/altuni_regression.txt): 145 unchanged and 4 changed, namely these 3 (ONTO-RELEASE) and Kristi-Regular 784->742. Kristi's release has OS/2 v1, which carries no x-height; its harness gate is CLEAN and identical to baseline/ (runs/altuni-kristi/). The 10 standard-height tests and 113 fontforge tests pass, and cargo fmt --check and clippy are clean (runs/cargo-test-altuni.txt). verify_heights_port agrees 42/42.
  Upstream: Yes. It is an additional commit on simoncozens/babelfont-rs#91 (pr-ff-os2-defaults), not a force-push, and Felipe pushes it. Suggested subject: 'Find a height glyph by an alternate codepoint too, as FontForge does'. Following Simon's style, the comment states only the format rule. All landings stay blocked until #91-#93 merge; this commit must be in the merged #91.
- **gf-source-modernization tools/sfd_edit.py (workspace)**: New op 'addprivate <Key> <value...>'. It inserts 'BeginPrivate: 1 / <Key> <len> <value> / EndPrivate' where FontForge's SFD writer puts it: after DisplaySize/AntiAlias/FitToEm/WinInfo/OnlyBitmaps and before Grid/TeXData/AnchorClass2/BeginSubFonts/BeginChars (sfd.c SFDDumpPrivate, called from SFD_Dump). It is FATAL if the source already has a private dictionary, and it reports 'no private dictionary' as the before-state.

  Evidence: make_edits.sh applies it to 13 sources, and each copy differs from its source by exactly the 3 added lines (runs/make_edits.txt). babelfont reads the section only for the height filter and does not emit it to .glyphs: the before->blues .glyphs diffs are the x/cap values only (runs/glyphs_diff-before-blues.txt).
  Upstream: No (workspace tool).
- **gf-source-modernization tools/ff_heights_oracle.py (workspace, optional)**: The same AltUni lookup for the Python oracle: parse AltUni2 lines and build by_uni in gid order over primary and alternate codepoints, as SFFindGID does. Without it the oracle and the fixed port can diverge under a glyph-count-mean rule, although the oracle models only the master rule today.

  Evidence: Under the master rule it changes nothing. The oracle output on families-next.tsv is identical before and after (runs/oracle-next-current.txt vs runs/oracle-next-altuni.txt, 62/103). verify_heights_port gives 42/42 with the patched oracle and either converter.
  Upstream: No (workspace tool).

## Families that land once these are in

- kottaone
- ledger
- lilitaone
- lustria
- macondo
- magra
- mergeone
- oleoscript
- oleoscriptswashcaps
- rambla
- rosarivo
- sail
- textmeone

## Decisions for Felipe

- Form of the 13 height edits. Recommended: (A) addprivate BlueValues, one edit per style. It restores the single input the exporter had, and the converter's own verified rule then yields both heights. The value comes from src/<X>.otf in the base tree. Alternative: (B) state the results with addfield OS2XHeight/OS2CapHeight, as the PatrickHand precedent did. That is 22 values, each derived by FontForge's rule with the .otf's BlueValues. Both close the same rows; only A was harness-run for all 13.
- Restore only BlueValues (recommended and verified; the only private entry that affects a TTF export), or the whole CFF Private dict FontForge read from the .otf: OtherBlues, StdHW/StdVW, StemSnapH/V and so on. The other entries change nothing in the TTF, so they cannot be checked against the release.
- Ledger: google/fonts 0436d99c0 and f8265bddf also bumped head.fontRevision and name to 1.002 and then 1.003. The gate does not block on these. Decide whether to add a setfield Version commit after the nbsp commit to mirror the bump, or leave it to future work.
- Push the #91 follow-up commit (probes/babelfont-altuni-lookup.patch) to pr-ff-os2-defaults. kottaone, macondo and rosarivo cannot land CLEAN without it.
- Commit the new sfd_edit.py op 'addprivate' (uncommitted in the working tree) together with investigations/next-heights/{probes,runs}. Nothing was committed, per the task.
- The magra, rambla and rosarivo siblings (Magra-Regular, Rambla-Italic, Rambla-Regular, Rosarivo-Regular) also lost their BlueValues in the re-import, but they are CLEAN, so under the workspace rule they get no edit. Confirm that per-style asymmetry within a family is acceptable.

## Unresolved

- Variation-sequence alternates are not modelled. FontForge's SCUniMatch compares alt->unienc even when the AltUni2 entry carries a variation selector, but babelfont's SFD reader leaves such entries out of glyph.codepoints. No style of either batch is affected (runs/altuni_regression.txt).
- Lookup order: FontForge takes the lowest gid; babelfont (and the patch) takes file order. These are the same for FontForge-saved SFDs.
- FontForge measured the unrounded in-memory quadratic splines after addExtrema/simplify/correctDirection (setquadraticaddextremasimplify-fontforge.py). The converter measures the re-imported, integer-rounded points. Here they give the same values on all 20 styles (16 in the unit plus the 4 CLEAN siblings), but the difference is not modelled in general.
- Scratch state, all regenerable: the patched converter's worktree /home/fsanches/compartilhado/sfd-reland-scratch/heights/bf-altuni, which is registered in integration-ff-prs's 'git worktree list' (remove it with git worktree remove once the patch is committed on pr-ff-os2-defaults); the binary in bf-target/; the edited .sfd copies in edits/ (make_edits.sh); FontForge C copies in ff/ (refetchable from raw.githubusercontent.com/fontforge/fontforge/<b69c9652760b|5a11aa4c0ab4|master>/fontforge/{fvfonts,splinefont,parsettf,sfd,tottf,splineorder2}.c); the harness build dirs in baseline/.
- Landing remains blocked for every family until babelfont #91-#93, with this follow-up, merge upstream (README policy). The weight-class rows depend on land.py's workaround until fontc is fixed.
- No FINDINGS.md or VERIFY.md was written, because the harness refuses report .md files. This result is the report.

## Rerun

    cd /home/fsanches/compartilhado/gf-source-modernization/investigations/next-heights/probes && bash rerun.sh probes
    bash rerun.sh builds   # sequential: runs.sh before|altuni|blues|final, gate_with_workarounds.sh, nothing_else_opened.sh, altuni_regression.py
    FAMILIES=/home/fsanches/compartilhado/gf-source-modernization/families-next.tsv BF=<17ea899 or patched> OUT=.../next-heights/runs/<set> TAG=heights-<set> SCRATCH=/home/fsanches/compartilhado/sfd-reland-scratch/heights [SRC_OVERRIDE=<edits>/<Style>-blues.sfd] bash /home/fsanches/compartilhado/gf-source-modernization/tools/baseline.sh <Style>
    /home/fsanches/compartilhado/gftools/venv/bin/python3 probes/altuni_regression.py <BF 17ea899> <BF patched>
    cd sfd-reland-scratch/heights/bf-altuni && CARGO_BUILD_JOBS=3 CARGO_TARGET_DIR=<scratch>/bf-target cargo test --release -p babelfont --features cli --lib fontforge_standard_height && cargo fmt -p babelfont -- --check && cargo clippy --release -p babelfont --features cli
