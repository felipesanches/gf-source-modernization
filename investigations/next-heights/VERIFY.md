# next-heights -- adversarial verification

**Model**: Claude Opus 5.5. Written from the verifier's structured result.

Reproduced: True

I reproduced every measurement independently. The task gave two output locations (next-
heights/verify/ and next-heights-verify/). I used the Files section's
/home/fsanches/compartilhado/gf-source-modernization/investigations/next-heights-
verify/{probes,runs}, and all scratch is under /home/fsanches/compartilhado/sfd-reland-
scratch/heights-verify/. Nothing was committed. The one-line command to regenerate
everything is probes/rerun.sh (probes|build|builds).

1. BEFORE. Harness tools/baseline.sh with FAMILIES=families-next.tsv and BF=integration-
ff-prs/target-heights (BUILT_FROM 17ea8995), unmodified sources. All 16 gates are line-
for-line identical to baseline-next/ (runs/before-vs-baseline-next.txt). There are 30
blocking rows: 24 OS/2 x/cap, 5 us_weight_class, 1 hmtx.uni00A0.

2. CONVERTER. I did my own build of the AltUni patch and did not reuse the
investigator's worktree: a `git archive 17ea899`, then `patch -p1 < next-
heights/probes/babelfont-altuni-lookup.patch`, drop-caches, then CARGO_BUILD_JOBS=3 with
target dir sfd-reland-scratch/heights-verify/bf-target. The source tree is not a
registered worktree (runs/BF-MINE.txt). Their worktree diff equals the patch file byte
for byte. fontforge_standard_height.rs is identical at 119f2be and 17ea899. Results:
- cargo test --lib fontforge: 113 passed, including the new
test_a_glyph_is_found_by_an_alternate_codepoint.    - cargo fmt --check: exit 0. clippy:
no warnings (runs/cargo-test-altuni.txt).    - Harness `altuni`: KottaOne, Macondo and
Rosarivo-Italic go from BLOCKING 1 to CLEAN 0.    - Conversion-only regression over all
149 styles of both batches (runs/altuni_regression.txt): 145 IDENTICAL and 4 changed.
The changes are KottaOne 81->76, Macondo 25->24, Rosarivo-Italic 229->217 and Kristi-
Regular 784->742. Kristi's release is OS/2 v1 (FFTM 2010), and the committed probe gives
742 under the 2011 rule, so the port is right there too.    - verify_heights_port with
my build: 42/42.    - The oracle patch changes no output on either batch (62/103 next,
first batch unchanged).

3. ALTUNI ARITHMETIC. I re-derived it with the committed ff_heights_probe
(runs/altuni_arith.txt):    - KottaOne: tops 480/485/495, sum 1460. 1460/19 = 76.84 (76)
and 1460/18 = 81.11 (81).    - Macondo: 456/19 = 24.0 and 456/18 = 25.33.    - Rosarivo-
Italic: 4138/19 = 217.79 and 4138/18 = 229.89. Its mu is pointy at 509, the same height
as the round c, e and o.    - FontForge C (fetched b69c9652760b, 5a11aa4c0ab4, master):
SFGetChar -> SFCIDFindCID -> SFFindGID -> SCUniMatch. SCUniMatch matches unicodeenc OR
any altuni->unienc, and the lowest gid wins. The function bodies hash identically at all
three revisions.    - Census: in both batches the only x/cap codepoint that can be
reached only through AltUni2 is U+03BC, in 40 styles. No cap codepoint is affected.

4. BLUEVALUES VALUES AND EDITS. I read the values myself from src/<X>.otf in
googlefontdirectory-hg 52f780bc with fontTools and formatted them as parsettf.c
realarray2str does. My 13 edited copies (probes/make_edits.py, runs/make_edits.txt) are
byte-identical to the investigator's edits/*.sfd. Each differs from its source only by
the 3 private-dictionary lines, plus Width 0->281 for Ledger. The block format matches
sfd.c SFDDumpPrivate (key, strlen(value), value) and the placement matches SFD_Dump's
order (after FitToEm, before BeginChars).

5. PROVENANCE. The investigator printed these facts but never drew the tie; I checked it
(runs/otf_head_dates.txt):    - For all 20 styles, the .otf's head.created equals the
release's FFTM sourceCreated.    - The .otf's head.modified comes 4-108 s before FFTM
sourceModified. That fits the HOWTOGEN ttx round trip followed by
setquadraticaddextremasimplify-fontforge.py.    - The -TTF.sfd CreationTime and
ModificationTime equal the FFTM source dates, which fits ttf2sfd.py importing the
release TTF.    - 19 of 20 releases are byte-identical to the hg binaries
(runs/release_vs_hg.txt).    - splineorder2.c never touches sf->private, so the
dictionary survives is_quadratic. tottf.c setos2 calls SFXHeight and SFCapHeight.    -
splinefont.c (b69c9652) snaps to every other BlueValues entry, starting from the first,
when the distance is strictly less than (ascent+descent)/100. babelfont's
snap_to_blue_zone matches this, with Ascender=Ascent and Descender=-Descent.

6. WHOLE-PROGRAMME CONSISTENCY. probes/blues_theory_all.py covers every style of both
batches with a sibling .otf that carries BlueValues: 86 styles, 172 height values. Using
the FFTM-selected rule with SFFindGID lookup, 151 values match with or without the .otf
blues, and 21 match only with them. None matches only without them (0 contradictions)
and none matches neither. The 21 blues-only values are exactly this unit's 21 blues
rows. probes/rule_all_next.py finds no height mismatch anywhere else in families-next,
including the BUILD-FAILED Cardo-Regular (900/1410 predicted = release). So the unit
misses no style.

7. BLUES, FINAL AND WORKAROUNDS.    - `blues` (BF 17ea899 + my edits): every targeted
row closes. Only the 5 us_weight_class rows remain.    - `final` (my patched BF +
edits): the same 5 rows remain.    - Adding tools/workarounds.py (TTFWeight as FEA)
makes all 16 styles CLEAN 0.    - The 4 CLEAN siblings stay CLEAN with the patched BF,
and their gates are identical to baseline-next.    - runs/nothing_else_opened.txt: a
full gate diff against `before` shows only the targeted BLOCKING lines and the summary
count changing. Stale lines are identical.    - The .glyphs diffs
(runs/glyphs_diff-{blues,altuni}.txt) show only the x/cap metric pos values and Ledger's
nbsp width. The 17 styles other than the three AltUni ones are byte-unchanged by the
patch.

8. LEDGER. runs/ledger_history.txt: hg 52f780bc = gf 90abd17b4 (nbsp 0, x 487).
0436d99c0 changed head, hmtx and name (nbsp 0->281, 1.002). f8265bddf changed head and
name only (1.003). OS/2 was never touched.

## Verdict

The investigation is correct in substance; only small corrections are needed. I reproduced all 30 blocking rows, which match baseline-next gate for gate. Both root causes reproduce independently.

1. The #91 lookup gap. FontForge finds 'mu' (U+00B5 with AltUni U+03BC) for U+03BC; babelfont misses it, so the 2011 glyph-count divisor is off by one: 19 against 18. My own build of the proposed patch closes KottaOne, Macondo and Rosarivo-Italic. It changes nothing else in 149 styles apart from Kristi's unshipped field, and its tests, fmt and clippy all pass.

2. The lost BlueValues. FontForge exported 13 releases from src/<X>.otf and snapped their heights to that file's CFF BlueValues; the -TTF.sfd re-imports the TTF and has no private dictionary. The values I re-derived give byte-identical edits, and the result is consistent across the whole programme: 0 contradictions in 86 styles. With those edits, the patched converter and land.py's existing weight-class workaround, all 16 styles are CLEAN, and no other gate line changes.

Ledger's nbsp row is google/fonts 0436d99c0, as claimed.

Corrections to fold in:
- Relabel us_weight_class from 'compiler-gap' to the programme's 'converter-fidelity'.
- 21 values, not 22.
- The no-edit asymmetry covers 7 styles, not 4.
- Qualify the HOWTOGEN and ttf2sfd paths in the commit bodies.
- Add the .otf head.created = FFTM sourceCreated tie as evidence.
- Note the GDEF U+0307 disclosure that 7 of these gates ask for.

What only Felipe can do: push the #91 follow-up commit, and decide whether to commit the addprivate op. Scratch under sfd-reland-scratch/heights-verify (bf-src, bf-target, edits, the regression and oracle copies) is disposable: probes/rerun.sh rebuilds all of it. The probes and runs to keep are in investigations/next-heights-verify/.

## Per edit

- [keep] Restore the BlueValues the release was exported with (Ledger-Regular, [-21 0 487 495 750 768]) -- I read the value from src/Ledger-Regular.otf CFF Private independently; the edited file is byte-identical to the investigator's. The rule gives flat 485.0, which snaps to 487 (distance 2). The harness closes OS/2.sx_height and nothing else changes. Optional body improvement (applies to all 12 BlueValues commits): 'tools/generate/HOWTOGEN.txt' and 'ttf2sfd.py' are not in the landed repository. Cite them as googlefontdirectory-hg 52f780bc paths, and add the direct tie: the .otf's head.created equals the release's FFTM sourceCreated.
- [keep] Give the no-break space the space's width, 281 (Ledger-Regular) -- google/fonts 0436d99c0 changed hmtx uni00A0 from 0 to 281. The .sfd states space Width 281 and uni00A0 Width 0. The row closes in my harness. Classed correctly as source-edit-from-release.
- [keep] Restore the BlueValues the release was exported with (LilitaOne-Regular, [-10 0 506 510 704 709]) -- Value re-derived. 500.0 snaps to 506 and 700.0 to 704. Both rows close; nothing else changes.
- [keep] Restore the BlueValues the release was exported with (Lustria-Regular, [-11 0 504 511 704 711]) -- Value re-derived. 511.0 snaps to the zone BOTTOM 504 (distance 7), which is correct because only even-index entries are candidates. 700 snaps to 704. Both rows close.
- [keep] Restore the BlueValues the release was exported with (Magra-Bold, [-12 0 525 537 700 712 750 760]) -- Value re-derived. 533 snaps to 525 and 708 to 700 (distance 8 each, under the tolerance of 10). Both rows close. Magra-Regular's .otf has identical BlueValues but Magra-Regular is CLEAN, so it correctly gets no edit.
- [keep] Restore the BlueValues the release was exported with (MergeOne-Regular, [-8 0 493 502 679 687]) -- Value re-derived. The 2012 rule gives 492.0, which snaps to 493; cap 679 is unaffected. The row closes.
- [keep] Restore the BlueValues the release was exported with (OleoScript-Bold, [-12 0 443 443 710 710]) -- Value re-derived. 436.5 snaps to 443 and 708.75 to 710; only the 2012 rule plus the blues gives both. Both rows close.
- [keep] Restore the BlueValues the release was exported with (OleoScript-Regular, [-12 0 443 450 710 710]) -- Value re-derived. 442.5 snaps to 443 and 709 to 710. Both rows close.
- [keep] Restore the BlueValues the release was exported with (OleoScriptSwashCaps-Bold, [-13 0 443 443 747 747]) -- Value re-derived. 436.5 snaps to 443 and 750.2 to 747. The .otf's own OS/2 cap height is 710, so the value is not a copy of the .otf's OS/2. Both rows close.
- [keep] Restore the BlueValues the release was exported with (OleoScriptSwashCaps-Regular, [-12 0 443 450 747 747]) -- Value re-derived. 442.5 snaps to 443; cap 747 is already exact. The row closes.
- [keep] Restore the BlueValues the releases were exported with (Rambla-Bold + Rambla-BoldItalic, [-13 0 517 524 669 680]) -- Both .otf files carry identical BlueValues (checked). 513 snaps to 517 and 668 to 669 in both styles. All 4 rows close. Rambla-Regular and Rambla-Italic (zones 506/668) are CLEAN and correctly get no edit.
- [keep] Restore the BlueValues the release was exported with (Sail-Regular, [0 0 389 389 666 666]) -- Value re-derived. Cap 665 snaps to 666. The x-height of 435 is 46 from zone 389, so it is unaffected. The row closes.
- [keep] Restore the BlueValues the release was exported with (TextMeOne-Regular, [-1 0 502 502 700 706]) -- Value re-derived. 500.0 snaps to 502; cap 700 is already exact. The row closes.

## Per tool change

- [keep] babelfont-rs follow-up commit on PR #91 (pr-ff-os2-defaults @119f2be): glyphs_by_primary_codepoint -> glyphs_by_codepoint (a glyph is found by any of its codepoints, first in order wins) + test_a_glyph_is_found_by_an_alternate_codepoint -- The change is faithful to FontForge. SFGetChar goes through SFCIDFindCID to SFFindGID and SCUniMatch, which match unicodeenc or any altuni with the lowest gid winning; the bodies are identical at b69c9652, 5a11aa4c and master. (The investigator's chain skips SFCIDFindCID, which changes nothing.) I rebuilt it independently from a git archive plus the patch. 113 tests pass, fmt and clippy are clean, 145 of 149 styles are unchanged, and the only 4 changes are the 3 targeted rows plus Kristi's unshipped field (742 = FontForge 2010 value). The harness closes 3 rows and opens nothing. It is small, self-contained and depends on no fork, so an upstream maintainer can merge it. It must be an additional commit on #91 that Felipe pushes, not a force-push. The doc comment names SFFindGID; the file already cites FontForge function names throughout, so it is consistent, but Simon may prefer the format rule alone.
- [keep] gf-source-modernization tools/sfd_edit.py new op 'addprivate <Key> <value...>' (uncommitted working-tree change) -- It writes exactly what FontForge's SFDDumpPrivate writes: 'BeginPrivate: 1', then '<key> <strlen> <value>', then 'EndPrivate'. The insertion point follows SFD_Dump's order (after DisplaySize/AntiAlias/FitToEm/WinInfo/OnlyBitmaps, before Grid/TeXData/AnchorClass2/BeginSubFonts/BeginChars). It is FATAL when a private dictionary already exists. land.py applies plan ops generically through sfd_edit.apply, so no other tool needs a change. My make_edits.py, which imports the op, produced files byte-identical to the investigator's. It still needs committing with the next-heights probes.
- [keep] gf-source-modernization tools/ff_heights_oracle.py: AltUni2-aware lookup (lowest gid over primary + alternate codepoints) -- optional -- It changes no oracle output on either batch (next: 62/103 before and after; first batch identical). It removes a blind spot the oracle shares with the unpatched port: verify_heights_port gave 42/42 while both ignored AltUni, so that cross-check could never have caught this bug. It is a workspace tool, so no upstream review is needed.

## Objections

- The us_weight_class rows (Magra-Bold, OleoScript-Bold, OleoScriptSwashCaps-Bold, Rambla-Bold, Rambla-BoldItalic) are classed 'compiler-gap', a label not used anywhere in the first batch's results. The first-batch precedent classes the same fontc 1.0.0 static-weightClass rows as 'converter-fidelity' (heights/results.json, nosifer, workflow journal). The substance is right: the .sfd states TTFWeight, tools/workarounds.py carries it, and all 5 are CLEAN in my final-workarounds runs. The label should be reconciled with the programme's vocabulary, or the vocabulary extended on purpose.
- No other objection. The 21 BlueValues rows are provenance, consistent with the PatrickHand precedent (release exported from the .otf, .sfd re-imported from the release). The 3 AltUni rows are converter-fidelity. Ledger's nbsp row is source-edit-from-release.

## Missed

- The strongest provenance fact is not stated. For all 20 styles, src/<X>.otf's head.created equals the release's FFTM sourceCreated, and its head.modified comes 4-108 s before FFTM sourceModified (runs/otf_head_dates.txt). The investigator's facts.txt printed both dates but never drew the tie. It ties each release directly to that .otf, not just to the generic HOWTOGEN procedure, and it belongs in each edit's value_derived_from.
- Arithmetic slip in decisions_for_felipe: alternative (B) is described as '22 values', but the blues rows total 21 x/cap values (Ledger 1, LilitaOne 2, Lustria 2, Magra-Bold 2, MergeOne 1, OleoScript-Bold 2, OleoScript-Regular 2, OleoScriptSwashCaps-Bold 2, OleoScriptSwashCaps-Regular 1, Rambla-Bold 2, Rambla-BoldItalic 2, Sail 1, TextMeOne 1).
- The asymmetry decision lists only the 4 CLEAN siblings (Magra-Regular, Rambla-Italic, Rambla-Regular, Rosarivo-Regular) as having lost their BlueValues. KottaOne-Regular, Macondo-Regular and Rosarivo-Italic lost theirs too, and they get no BlueValues edit either: 7 styles in total. This is harmless, because their glyph-count-mean heights (76/212, 24/53, 217/224) are nowhere near a zone, but the decision as stated to Felipe is incomplete.
- Commit bodies cite 'tools/generate/HOWTOGEN.txt' and 'ttf2sfd.py' as bare paths. Neither exists in the landed repository, whose first commit holds only ofl/<family>/, so they should be qualified as googlefontdirectory-hg 52f780bc tools/... paths.
- Not a height row, but relevant to 'families_landable_after': 7 of the 16 gates (KottaOne, Lustria, Macondo, OleoScript-Bold, OleoScript-Regular, OleoScriptSwashCaps-Bold, OleoScriptSwashCaps-Regular) carry the gate's non-blocking note 'GDEF.glyph_classes -- our build corrects 1 mark class(es) the release got wrong: U+0307. Disclose in the PR body'. tools/pr_body.py has no hook for it (grep finds no 'Disclose'/'GDEF'), so the disclosure has to be added by hand or the recipe decision (--infer-mark-category) revisited under the equivalence rule.
- Hygiene, which the investigator disclosed: their scratch worktree sfd-reland-scratch/heights/bf-altuni is registered in the shared babelfont repo's worktree list (integration-ff-prs 'git worktree list' line 25) and has to be removed with 'git worktree remove'. A git-archive export (as used here) avoids registering anything.
- Confirmed nothing missed in scope: no other style in either batch needs the BlueValues edit (blues_theory_all: 0 contradictions, 0 unexplained over 86 styles / 172 values), and no other next-batch style has a height mismatch under FontForge's rule (rule_all_next.txt). The pairing (families-next.tsv, FontName match, -TTF variant, 1 candidate each) and the .otf-by-name pairing were checked against the CFF FontNames; all agree.
