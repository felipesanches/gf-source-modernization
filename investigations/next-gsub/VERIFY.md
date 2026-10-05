# next-gsub -- adversarial verification

**Model**: Claude Opus 5.5. Written from the verifier's structured result.

Reproduced: True

I reproduced every substantive claim with my own runs, and most of them with my own probes. Everything is under /home/fsanches/compartilhado/gf-source-modernization/investigations/next-gsub-verify/ (README.txt lists each probe's question and command). Scratch is /home/fsanches/compartilhado/sfd-reland-scratch/gsub-verify/. Nothing is committed. What is in scratch can be regenerated from README.txt.

Pairing: I used families-next.tsv as is. There is 1 candidate per style, each an -TTF.sfd at hg 52f780bc. Each release is byte-identical to its hg blob (Megrim.ttf git blob 8fc9351c). For all 5 releases, the FFTM created/modified times equal the .sfd's CreationTime/ModificationTime (runs/release_facts.txt).

v0, the unmodified sources with integration 17ea899, is identical to baseline-next: Megrim 4, Poly-Italic 3, RibeyeMarrow 2, Varela 6, Poly-Regular CLEAN. The releases register all 72 GSUB lookups (Poly-Italic 19, Poly-Regular 14, RibeyeMarrow 8, Varela 31) exactly as the .sfd states. Lookup types pair up in file order (runs/sfd_registration_vs_release.txt).

Megrim:
- The release has no GSUB, GPOS, GDEF, DSIG or kern. usMaxContext is 1, and the FFTM build stamp is 2011-02-22 13:48:33.
- I fetched v20110222 tottf.c and read initATTables. It confirms that GSUB/GPOS/GDEF/DSIG are written only in opentypemode, and legacy kern only when OpenType and Apple modes are both off.
- The 4 Jura TTFs were created 93-107 s after Megrim. They carry kern only, and their .sfd files declare abvm/blwm/kern.
- My own sfd_edit.py droplookup x3 gives a file byte-identical to edits/Megrim.droplookups.sfd: 25 lines removed. Y -> y.ss01 is confirmed.
- With the edits, v1 (17ea899) and v3 (prototype) leave only OS/2.us_weight_class. Adding the tools/workarounds.py weight class gives CLEAN 0 on both (runs/v4-*). v0 plus the workaround leaves the 3 GSUB rows.

Babelfont prototype:
- I built it myself from the published diff (git apply on 17ea899; BUILT_FROM d345b49). The next-emptygpos patch applied with git am gives an identical tree.
- v2: Poly-Italic CLEAN 0, Poly-Regular CLEAN 0, Varela BLOCKING 3 (GPOS.* only), RibeyeMarrow still 2 under the shared gate.
- My structural probe (gsub_langsys_semantics.py resolves each language system, expands nested lookups, and ignores lookup index, 5-vs-6 type, packing, and ligature or disjoint-rule order) reports:
  - v0: Poly-Italic latn/ROM gains aalt. Varela latn/AZE, CRT and TRK inherit liga lookup 24 and smcp lookup 21, and latn/SRB gains aalt. RibeyeMarrow is already equal.
  - v2: 0 of 2, 0 of 10 and 0 of 1 language systems differ.
- HarfBuzz with forced x-hbot<TAG> languages (shape_langsys.py) gives the same result:
  - v0: Varela TRK/AZE/CRT 'fi' -> fi in the build but f+i in the release. Under SRB with aalt, 30411 of 30578 runs differ.
  - v2: glyph sequences are identical everywhere.
  - v2 advance-only residues:
    - Poly-Italic, 102 runs: U+0307/U+0326, the GDEF mark-class RELEASE-STALE row.
    - RibeyeMarrow, 84 runs: U+0312/U+0315/U+0326, same row.
    - Varela, 190 runs: all i+U+0307 with .notdef advance 514 vs 0. It disappears when the release's empty GPOS is copied in (runs/varela_residual_gpos.txt), so it belongs to the empty-GPOS unit.
- fea-rs 1.0.0 source confirms the mechanisms: features.rs finalize_aalt registers aalt for every default language system. validate.rs allows only Gsub1/Gsub3/feature refs in aalt. features.rs set_system copies the script-default lookups on the first `language` statement unless exclude_dflt. contextual.rs into_lookups picks Chain only if a rule has backtrack or lookahead.
- babelfont's hoist rule is confirmed in fontforge.rs.
- cargo fmt --check is clean. clippy --all-targets gives 0 warnings. cargo test --release --lib fontforge: 114 passed, 0 failed, including both new tests. My filter differs from their '80 -> 82'.

Scope of the change:
- A static scan of all 149 paired sources (sfd_langsys_scan.py) and a conversion sweep with both converters (fea_sweep.sh) agree. The FEA changes for exactly Megrim, Poly-Italic and Varela in the next batch (104 identical), and for their 9 first-batch r5 styles.
- Only Play-Regular hits the aalt warn-only branch.

Gate:
- The proposed gate takes RibeyeMarrow from 2 to 0 on my v0 and v2 builds. The trace confirms the shared gate refuses on the type alone ('rules differ; types False').
- A re-run of their gate_sweep.sh is identical to theirs: RibeyeMarrow is the only verdict that changes.
- Their gate_ctx_negative.py on my v2 builds reproduces their verdicts: shared gate unsound 2 on Varela ordn and a false block on RibeyeMarrow frac; proposed gate unsound 0.
- I closed their open first-batch gap. On 7 first-batch styles whose releases carry contextual GSUB (Kristi, AbrilFatface, Lekton x2, PatrickHand, Tuffy x2; runs/v6-first-batch-ctx), both gates give identical blocking sets. In 5 of them the proposed gate exercised and accepted the contextual rule comparison.

## Verdict

The investigation holds up. Every table row, cause, edit value and measurement I re-derived reproduces:
- Megrim was a FontForge 20110222 OpenType-off export, and the three droplookup edits plus the existing weight-class workaround give CLEAN 0.
- Poly-Italic and Varela carry converter-fidelity registration errors (inherited default lookups, aalt on every languagesystem). The exclude_dflt and aalt prototype, rebuilt by me from the published diff, makes all 12 language systems equal (Poly-Italic 2 and Varela 10) structurally and under HarfBuzz.
- RibeyeMarrow is functionally equal and blocked only by the shared gate's type check. The proposed gate resolves it without changing any other next-batch or first-batch verdict I tested.

Corrections:
- 3 conservative refusals, not 4.
- The aalt heuristic's warn-only gap already occurs in Play-Regular.
- The diff needs rebasing before an upstream PR, and exclude_dflt should be filed separately from the aalt heuristic.

Outside the GSUB rows, the 'landable' list should carry two caveats: the gate-accepted GDEF mark-class advance changes, and Megrim's family/PostScript naming. Confidence: high.

## Per edit

- [keep] Drop the aalt lookup the release does not carry -- The source lines are confirmed: line 56 plus 11 Substitution2 entries (M N R U V W Y i m w y). Each piece of the origin evidence checks out independently: - the release's table set and usMaxContext 1; - the FFTM build stamp 2011-02-22, with FFTM modified == .sfd ModificationTime 2011-04-28 15:00:19; - v20110222 initATTables writes GSUB/GPOS/GDEF/DSIG only in opentypemode; - the same-session Jura exports have kern only. Nothing is copied from the binary. My sfd_edit.py application is byte-identical to theirs. v1 and v3 leave only us_weight_class, and with the workaround both are CLEAN 0. This matches the Nosifer precedent Felipe settled on 2026-09-24.
- [keep] Drop the ss01 lookup the release does not carry -- Line 57 plus 10 Substitution2 entries. The blank script tag maps to DFLT. The source maps capital Y to y.ss01 (StartChar Y at line 6296 -> y.ss01), as they note. Same evidence and verification as the aalt edit.
- [keep] Drop the Turkish locl lookup the release does not carry -- Line 58 plus 1 Substitution2 entry (i -> i.TRK, latn/TRK only). Same evidence. The three edits in plan order apply cleanly. droplookup's still-referenced check passes. The combined result is CLEAN 0 with the weight-class workaround on both converters (runs/v4-megrim-v1+workarounds, v4-megrim-v3+workarounds).

## Per tool change

- [keep] babelfont-rs layout.rs make_langsys: `language XXX exclude_dflt;` for every language other than dflt -- The change is correct and minimal. fea-rs 1.0.0 features.rs set_system copies the (script, dflt) lookups registered so far into a non-dflt language on its first `language` statement unless exclude_dflt is set. It uses entry().or_insert_with, so later statements do not reset the list, and exclude_dflt reproduces FontForge's per-language registration exactly.  Verified on my own build of the published diff: - Varela: 10 of 10 language systems are structurally equal, and HarfBuzz glyph output is identical under every forced language system. - fmt is clean and clippy reports 0 warnings. - 114 fontforge-filtered tests pass, including test_language_does_not_inherit_default_lookups. - The conversion sweep changes the FEA of 12 of 149 styles: Megrim, Poly-Italic, Varela, and the 9 first-batch r5 styles, whose gate rows are unchanged.  Before filing: the diff is made against integration 17ea899. Its source hunks apply to upstream main 496e904, but the tests.rs hunk does not, because its context comes from pr-ff-reader-fixes (#91). The PR must be rebased onto upstream main, or stated as stacked on #91.
- [revise] babelfont-rs fontforge.rs: declare only aalt's language systems when aalt is narrower and no kerning or anchors exist -- It works where it applies. Poly-Italic latn/ROM and Varela latn/SRB lose the extra aalt: Poly-Italic is CLEAN 0 and Varela is semantically equal in every language system. fea-rs indeed allows no script/language inside aalt and registers it for every languagesystem, so an FEA-level workaround is the only converter-side option.  It is still a heuristic, and the gap it warns about is not hypothetical. In their own r5 run and in my sweep, Play-Regular (first batch) takes the warn-only branch: aalt lacks latn/AZE, CRT, MOL, ROM and TRK, and kerning or anchors are present. Their result does not report this. Play has no practical impact now, because it is being re-landed from alexeiva/play.  Revisions: - File it as a separate PR from exclude_dflt, so the uncontroversial fix is not held up by a design discussion with Simon. - Name Play-Regular as a real warn-only case. - Apply the same rebase as the exclude_dflt change.
- [keep] table gate: arbitrate_gsub_lookup_order compares contextual lookups by rules per first glyph (table_gate_gsub_proposed.py, wrapper over the shared 2f43693) -- This remains a proposal for Felipe, since table_gate.py is our own tool.  Reproduced: - RibeyeMarrow goes 2 -> 0 on my v0 and v2 builds. - The sweep re-run is identical: only RibeyeMarrow changes, and Cardo-Regular is skipped. - Their negative-test probe on my builds gives the same verdicts: shared gate unsound 2 on Varela ordn; RibeyeMarrow frac shared false block, proposed sound.  I added first-batch coverage: Kristi, AbrilFatface, Lekton x2, PatrickHand and Tuffy x2 give identical blocking sets under both gates.  Correction: their outputs show 3 behaviour-neutral mutations refused conservatively (varela-frac swap and retarget, varela-ordn swap), not 4.  Residual looseness, not introduced by this change: nested non-contextual lookups compare ligatures as sorted rules, which ignores ligature-order shadowing. The shared gate compares only ligature counts.

## Objections

- No row is misclassified. Every cause was reproduced from the paired source under families-next.tsv.
- Nuance (not an error) on Poly-Italic and Varela feature_list/lookup_list: they are 'gate-arbitration' only in the sense that the EXISTING shared gate accepts them once the language-system fix removes the real registration difference. They need no gate change. For Varela, that acceptance is weak evidence: the shared gate's languages omit AZE, CRT and MOL, and its corpus does not reach ordn, as the negative test shows. The equality rests on the structural and shaping probes, and theirs and mine agree.
- Varela GPOS.* is correctly attributed to the empty-GPOS unit. The one residual shaping difference after the babelfont change (i+U+0307, .notdef advance 514 vs 0) disappears when the release's empty GPOS is copied into the build (runs/varela_residual_gpos.txt).

## Missed

- Play-Regular (first batch) triggers the aalt heuristic's warn-only branch, and their own runs/r5-first-batch-regression/proto/Play-Regular.gate.txt logs the warning. The result instead says no style in this unit hits it, which implies the gap is hypothetical. It is real in the 149-style corpus. There is no practical effect while Play is re-landed from alexeiva/play.
- The babelfont diff does not apply to Simon's upstream main 496e904: the tests.rs hunk context comes from PR #91. The source hunks apply. 'upstream_pr_needed' should state the base, meaning rebase onto upstream main or stack on #91.
- Miscount: the proposed gate refused 3 behaviour-neutral mutations, not 4 (their runs/gate_ctx_negative.*.txt).
- The 'landable CLEAN' claims rest on the gate accepting GDEF mark-class RELEASE-STALE rows, and those rows change shaping advances in all three OpenType styles. Measured on the v2 builds: Poly-Italic U+0307/U+0326 (102 runs), RibeyeMarrow U+0312/U+0315/U+0326 (84 runs), and Varela U+0309/U+031B/U+0323, which the gate lists. The build zeroes these marks and the release does not. This is outside GSUB, but it conflicts with the 2026-09-24 'defects included' rule and should be a stated decision, not a silent acceptance. They mentioned only RibeyeMarrow's advance-only runs.
- Megrim naming is broader than the file name. The gate skips the name table by design ('disclosed separately'), but the build and release differ in several fields: - nameID 1: 'Megrim Medium' vs 'Megrim' - nameID 2: 'Regular' vs 'Medium' - nameID 4/6: 'Megrim Medium'/'Megrim-Medium' vs 'Megrim'/'Megrim' - fsSelection: 192 vs 64 METADATA.pb expects filename Megrim.ttf and post_script_name Megrim. Separately, the release is TrueType-hinted from the .sfd (cvt/fpgm/prep and 346 glyphs with TtInstrs), while the build has prep only, so it renders differently; the gate accepts this by design, and Varela's 834 hinted glyphs are affected the same way. Both points are outside this unit, but 'megrim landable' is overstated until naming is handled.
- Clarification, not an error: 26 next-batch releases lack both GSUB and GPOS. Their '18 with no layout tables' excludes the 8 that carry only a legacy kern table (Smokum, Ultra, KellySlab, Marvel x4, Wallpoet). Those 8 are also OpenType-off exports like Nosifer, but each source declares only its kern lookup, so Megrim remains the only next-batch style that loses GSUB lookups.
