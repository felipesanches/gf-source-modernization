# next-emptygpos -- investigation findings

**Model**: Claude Opus 5.5 (investigating agent, adversarial verifier, and the
conclusion below). Written from the agents' structured results (`results.json`).

## Conclusion

FontForge writes an empty GPOS sharing GSUB's script list when only GSUB has lookups;
it is functional (HarfBuzz skips fallback mark positioning when a GPOS exists). Closing
it needs a fontc/fea-rs option to share the script list, a gftools-builder3 config key,
and two babelfont language-system fixes (exclude_dflt; aalt's language systems). The
verifier refuted Ultra's proposed edits: its release was exported from googlefontdirectory-hg
2d042ebbd's Ultra-TTF.sfd, which needs no edit -- the pairing uses a later re-save.

## Investigator's report

Pins: babelfont integration-ff-prs 17ea899 (sha256 4cbc83e0), gftools-builder3 e851b8b
with fontc 1.0.0 (d6dd442c), table_gate 2f43693 (939a987f), diffenator3 1.1.4, fontTools
4.61.1, uharfbuzz 0.53.3 / HarfBuzz 12.3.2, google/fonts b5efa9c32e8f. All four styles
were built and gated with the harness; pairing is from families-next.tsv, and
families.tsv for UnifrakturMaguntia. Prototypes: fontc-v1.0.0 plus the shared-layout-
scripts patch built into builder3 (734e373e), and babelfont 17ea899 plus 2 commits
(864f649a). With the prototypes and `sharedLayoutScripts: true`, Varela is CLEAN and
UnifrakturMaguntia keeps only its 2 unrelated vmetric rows. The empty-GPOS rows close
with no other table change, and HarfBuzz horizontal shaping goes to 0 differing runs for
both (shape_compare, pair_matrix). Smokum and Ultra were mis-scoped: their releases are
kern-only, so the tool change does not apply and their rows need a decision.

Rows before: 17: Smokum-Regular 3 (GPOS x3), Ultra-Regular 3 (GPOS x3), Varela-Regular 6 (GPOS x3, GSUB x3), UnifrakturMaguntia-Book 5 (GPOS x3, hhea.descender, OS/2.us_win_descent), in runs/00-baseline

Rows after: 8: Smokum-Regular 3, Ultra-Regular 3, Varela-Regular 0, UnifrakturMaguntia-Book 2 (hhea.descender, OS/2.us_win_descent), in runs/10-all-prototypes. The fontc/builder3 change alone (runs/04): Varela 3, UnifrakturMaguntia 2. babelfont alone (runs/11): Varela 3 (GPOS).

Confidence: High on causes: every value was reproduced from FontForge source at the exact build the FFTM stamp names, and the shell's effect was measured with HarfBuzz before and after. High that the fontc prototype reproduces FontForge's GPOS shell for all 5 empty-GPOS releases with no other change. Medium on upstream acceptance: fontc may prefer a post-processing step. Medium on the aalt languagesystem rule, which is a conditional heuristic babelfont's maintainer may want shaped differently. The Smokum/Ultra outcome depends on Felipe's decision.

## Rows

| style | row | class | cause |
|---|---|---|---|
| Smokum-Regular | GPOS.script_list | decision | NOT an empty GPOS: the task premise is wrong for this style. The release has no GPOS, GSUB or GDEF, only a legacy `kern` table (format 0, 3904 pairs). FontForge v20110222 wrote it with OpenType output off. The FFTM stamp 3381227313 minus 2082844800 = 1298382513, exactly LibFF_ModTime of the v20110222 tarball. The hg binary at 52f780bc already has this layout; google/fonts hotfix 0e5ac906d changed only head/name. In tottf.c:5306, initATTables writes `kern` only when neither applemode nor opentypemode is set. Our build kerns through GPOS, because fontc cannot write a legacy `kern`. The gate's arbitrate_legacy_kern refuses because 28 pairs whose first glyph is U+00AD shape differently. HarfBuzz's kern-table machine puts kern1=v>>1 on the hidden soft hyphen's advance, which is then zeroed, and kern2 on the next glyph. GPOS puts the whole value on the hidden glyph, so the next glyph does not move. No combining marks, so fallback positioning plays no part. The empty-GPOS tool change cannot touch this row. |
| Smokum-Regular | GPOS.feature_list | decision | Same as GPOS.script_list: the legacy `kern` (FontForge v20110222, OpenType off) is modernised into a GPOS `kern` feature. Only U+00AD-first pairs shape differently. |
| Smokum-Regular | GPOS.lookup_list | decision | Same as GPOS.script_list. |
| Ultra-Regular | GPOS.script_list | decision | NOT an empty GPOS. As with Smokum, the release is a legacy `kern` only (2721 pairs), exported by FontForge v20110222 with OpenType off; the hg Ultra.ttf differs from the release only in head/name (hotfix 57fc85106). Three separate HarfBuzz differences follow. (1) Marks: the release has no GPOS, so HarfBuzz applies fallback positioning to its combining marks U+0312, U+0315 and U+0326; our GPOS turns that off (2211 LTR pairs). (2) Kerning class 0: FontForge's legacy-kern writer decomposes kern classes from first class 1 up (splinesaveafm.c:2038, SFKernClassTempDecompose). The source's KernClass2 '26+ 27' lists first class 0, the A group, so the release has no A-first pair; our GPOS kerns AT, AV, AW, AY, A-quote and so on (650 pairs). (3) The U+00AD split, as in Smokum (17 pairs). Provenance: the committed .sfd is newer than what was exported. FFTM sourceModified is 1304463351 (2011-05-03); the .sfd ModificationTime is 1318899232 (2011-10-18). |
| Ultra-Regular | GPOS.feature_list | decision | Same as Ultra GPOS.script_list: legacy kern-only release versus GPOS kerning. |
| Ultra-Regular | GPOS.lookup_list | decision | Same as Ultra GPOS.script_list. |
| Varela-Regular | GPOS.script_list | compiler-gap | FontForge's shared-script GPOS shell: scripts cyrl, grek and latn, each with only an empty dflt LangSys, 0 features and 0 lookups. In FontForge v20110222 (confirmed by exact FFTM match), SFScriptsInLookups (lookups.c:298) ignores its gpos argument and collects the scripts of both tables. SFLangsInScript gives a script with no lookups in a table a dummy DEFAULT_LANG ('This is what VOLT does'). dumpg___info (tottfgpos.c:3026) writes a table that has scripts and no lookups ('to get around a bug in Uniscribe'). FontForge master 67dd7dc9 still does all of this. fea-rs cannot emit such a table: PosSubBuilder::build_raw returns None without lookups or features (fea-rs/src/compile/lookups.rs:1425 at fontc-v1.0.0), and only `size` gets a lookup-less feature (:984). The shell is functional: with no GPOS, HarfBuzz fallback-positions U+0309, U+031B and U+0323. |
| Varela-Regular | GPOS.feature_list | compiler-gap | Same as Varela GPOS.script_list: FontForge's shell carries 0 features. |
| Varela-Regular | GPOS.lookup_list | compiler-gap | Same as Varela GPOS.script_list: FontForge's shell carries 0 lookups. |
| Varela-Regular | GSUB.script_list | converter-fidelity | babelfont writes FontForge's per-language lookup registrations as `script X; language Y;`, which leaves include_dflt on (make_langsys, layout.rs:262, LanguageStatement::new(lang, true, false)). So latn AZE, CRT and TRK inherit the latn/dflt lookups that the .sfd deliberately withholds from them: liga lookup 24 (fi/fl) and smcp lookup 21. FontForge registers every lookup explicitly and inherits nothing. Separately, aalt may carry no script or language statement in FEA, so it is registered under every `languagesystem`, including latn/SRB; the .sfd registers aalt for every language except SRB. The ordn chaining lookup is packed into 2 subtables instead of FontForge's 4, which does not change shaping. |
| Varela-Regular | GSUB.feature_list | converter-fidelity | Same as Varela GSUB.script_list: the inherited liga/smcp lookups for AZE/CRT/TRK and the extra latn/SRB aalt change which feature records each LangSys points to. |
| Varela-Regular | GSUB.lookup_list | converter-fidelity | Same cause; lookup order differs too, because fontc places the lookups referenced by the chaining lookups earlier. The order itself is inert: once the registrations are fixed, the gate's lookup-order arbitration accepts 102,400 identical shaped runs across 8 languages. |
| UnifrakturMaguntia-Book | GPOS.script_list | compiler-gap | FontForge v20100501's shared-script shell: DFLT, hani and latn, each with only an empty dflt, 0 features and 0 lookups. The mechanism is the same as Varela's (first-batch investigations/unifraktur). Without it, HarfBuzz fallback-positions 9 combining marks. |
| UnifrakturMaguntia-Book | GPOS.feature_list | compiler-gap | Same as UnifrakturMaguntia GPOS.script_list. |
| UnifrakturMaguntia-Book | GPOS.lookup_list | compiler-gap | Same as UnifrakturMaguntia GPOS.script_list. |
| UnifrakturMaguntia-Book | hhea.descender | converter-fidelity | Offset-mode hhea descender (HheadDescent -16, HheadDOffset 1). FontForge 20100501's sethhead bases it on int() of the true minimum (glyph J, -497.58, truncated to -497), giving -513. babelfont 17ea899 (with #85's floor/ceil) floors to -498 and gives -514. This is the pre-2014 vintage rule the first-batch investigation proposed; it is not implemented. Outside this unit's tool change. |
| UnifrakturMaguntia-Book | OS/2.us_win_descent | converter-fidelity | Offset-mode win descent (OS2WinDescent 16, OS2WinDOffset 1). Before ee15007274e9 (2014), FontForge's head bbox counts only on-curve points. J's lowest implied on-curve point is -495.5, which floors to -496, so 496+16 = 512. babelfont floors the true minimum (-498) and gets 514. Not implemented. |

## Proposed .sfd edits

- **Set TTFWeight to 400, the weight class Ultra was released with** (Ultra-Regular) `setfield TTFWeight 400` -- verified: True; value from: The release's OS/2.usWeightClass 400, copied from the binary. The release and the hg Ultra.ttf at 52f780bc have identical OS/2; google/fonts hotfix 57fc85106 changed only head/name. That binary is FontForge 20110222's export of the source as it stood on 2011-05-03 (FFTM sourceModified 1304463351), earlier than the committed .sfd (ModificationTime 1318899232).; the source stated: TTFWeight: 900
- **Set Weight to Regular, as the released Ultra is named** (Ultra-Regular) `setfield Weight Regular` -- verified: True; value from: nameID 2 'Regular' and family 'Ultra' of the hg Ultra.ttf at 52f780bc, FontForge 20110222's export, which predates the .sfd save. The release's nameID 4/6 ('Ultra Regular', 'Ultra-Regular') come from google/fonts hotfix 57fc85106 and match what babelfont builds after this edit.; the source stated: Weight: Black
- **Drop kerning class 0's row, as the released kern table has no A-group pairs** (Ultra-Regular) `kernclass0zero 'kern' Horizontal Kerning in Latin lookup 0 kerning class 1` -- verified: True; value from: FontForge v20110222 splinesaveafm.c:2038 (`for ( i=1; i<kc->first_cnt; ++i )`, quoted in probes/ff-excerpts.txt), and the release's kern table, which has 0 pairs with an A-group first glyph out of 2721. A later addition to the .sfd would explain the release equally well, since the .sfd postdates the export; the edit is the same either way.; the source stated: KernClass2: 26+ 27; first-class-0 (A Agrave ... Aogonek) row = [0,-55,-60,-60,-50,-40,-20,-20,-20,-20,-100,-80,0 x15]

## Proposed tool changes

- **fontc (fea-rs + fontir + fontbe + fontc CLI)**: An opt-in shared GSUB/GPOS script list, default off. fea-rs gets Opts::share_script_lists(bool). After AllLookups::build assigns features, every script present in either table is added to the other with an empty default LangSys (0xFFFF, no features) if it is missing; a table's own languages are untouched. PosSubBuilder::build_raw no longer returns None when scripts exist, so a table with scripts but no features or lookups is written. fontir gets Flags::SHARED_LAYOUT_SCRIPTS, fontbe passes it to the feature compile (on main, both compile and compile_merged), and the fontc CLI gets --shared-layout-scripts. This is VOLT's convention and FontForge's exporter rule (lookups.c SFScriptsInLookups/SFLangsInScript, tottfgpos.c dumpg___info, unchanged from 2010 to master 67dd7dc9). It is the only way to reproduce the empty GPOS, which suppresses HarfBuzz's fallback mark positioning. FEA cannot express it, and fontmake/feaLib does not emit it either.

  Evidence: Rows: Varela 6->3 and UnifrakturMaguntia 5->2 (runs/04), with nothing else changed (flag-off control runs/03 is identical to the pinned builds except head.modified and the nameID 5 stamp). The produced GPOS matches the release structurally in all 5 empty-GPOS styles (Varela, UnifrakturMaguntia, Kristi, Lekton-Bold, Lekton-Regular; runs/04 and runs/15). Horizontal HarfBuzz runs: Varela 28,272->0, UnifrakturMaguntia 32,256->0. 4 new fea-rs unit tests pass, and on upstream main 66637808 the fea-rs opts tests and fontc's args test pass, with clippy --all-targets and fmt clean. The existing fea-rs fonttools_tests cvparam_null.fea compare failure also happens on the untouched fontc-v1.0.0 tag with local fontTools 4.61.1.
  Upstream: googlefonts/fontc: one PR (the main-based patch), then a fontc release. The upstream-facing text should say it is opt-in, default off, and matches VOLT/FontForge output.
- **gftools-builder3**: FontcConfig gets `sharedLayoutScripts: bool` (default false), which maps to Flags::SHARED_LAYOUT_SCRIPTS. It is flattened into GoogleFontsOptions like reverseOutlineDirection, so a repository's sources/config.yaml can ask for it. The dependency must also move to a fontc release that carries the flag.

  Evidence: Built at e851b8b with a crates.io patch pointing at the fontc prototype; Cargo.lock changed only for the patched path crates, with no version bumps. runs/04, runs/10 and runs/15 use that binary (sha256 734e373e23e3...). fmt clean.
  Upstream: simoncozens/gftools-builder3: one PR, after the fontc release.
- **babelfont-rs (FontForge importer)**: make_langsys writes `language XXX exclude_dflt;` for every language other than dflt. A FontForge lookup applies to exactly the languages it names, and FEA's default include_dflt adds the script's dflt lookups to every other language.

  Evidence: Varela: TRK/AZE/CRT no longer get fi/fl (liga lookup 24) or smcp lookup 21; langsys differences 16->10 keys. A new unit test passes, all 70 FontForge tests pass, and clippy --all-targets and fmt are clean. The whole babelfont suite has 258 passing and 11 failing tests; the 11 read the external noto-cjk-varco checkout, which is absent, and are unrelated. Regression screen over all 149 styles in families.tsv and families-next.tsv (probes/fea_diff_sweep.sh): the FEA changes for 12 styles. Built with old and new converters, 10 have identical rows, Poly-Italic goes 3->0 and Varela 6->3 (runs/12-babelfont-regression, runs/11).
  Upstream: simoncozens/babelfont-rs: new PR (independent of #91/#92/#93), which can be combined with the next item.
- **babelfont-rs (FontForge importer)**: FEA forbids script/language statements inside aalt, so aalt is registered under every `languagesystem`. FontForge registers it only where its aalt lookups say. Every other FontForge lookup is written with explicit script/language statements. So when the converted font has no kerning and no anchors (the only features a compiler generates from the languagesystems), declare as `languagesystem` only aalt's (script, language) pairs. Otherwise keep all pairs and warn.

  Evidence: Varela GSUB 3->0 with babelfont alone (runs/11); aalt/sr cases 4->0. Poly-Italic 3->0 (its only GSUB difference was latn/ROM aalt). No style regressed among the 12 whose FEA changed. A new unit test (test_aalt_keeps_its_own_language_systems) passes.
  Upstream: simoncozens/babelfont-rs: same PR as exclude_dflt, or a second commit in it.
- **sfd-reland tools (recipe.py, baseline.sh, land.py)**: Our own harness. Let the recipe also emit builder3 config lines, and write `sharedLayoutScripts: true` into sources/config.yaml only when the release has FFTM AND a GPOS with 0 lookups AND a GSUB with lookups (FontForge's empty GPOS shell). baseline.sh needs B3 and EXTRA_CONFIG overrides, as in probes/baseline_b3.sh. Do NOT enable it for every FontForge OpenType-mode release: fontc's generated kern registers DFLT (and sometimes grek/cyrl) where FontForge's kern lookup did not, so the mirrored GSUB shell opens GSUB.script_list rows.

  Evidence: probes/recipe_shared_scripts.py selects 5 styles (runs/recipe_shared_scripts.tsv). Narrow rule, real builds: Kristi, Lekton-Bold and Lekton-Regular keep their rows (CLEAN / 1 weight row / CLEAN) and gain the release's exact GPOS (runs/15); Varela and UnifrakturMaguntia close 3 rows each. Broad rule, swept over 81 next-batch FontForge OpenType-mode builds (probes/shared_scripts_sweep.sh, runs/13-shared-scripts-sweep-next.tsv): opens GSUB.script_list in 33 styles and closes rows only in Varela. Census of 149 styles: runs/census_layout_shells.tsv.
  Upstream: none (this workspace)
- **sfd-batch5 tools/table_gate.py (arbitrate_legacy_kern)**: The legacy-kern arbitration shapes only the release's own pairs. It misses two things. First, HarfBuzz fallback mark positioning: a kern-only release has no GPOS, so HarfBuzz positions its marks, and the build's GPOS switches that off. Second, pairs that only the build kerns. It should refuse when the release has combining marks in its cmap and no GPOS while the build has one, and it should shape the full LTR pair matrix (probes/pair_matrix.py), not just the release's kern pairs.

  Evidence: Fidelity-only builds of landed or accepted kern-only styles. Miama-Regular (landed CLEAN 2ff6126): 73,583 of 1,232,100 LTR pairs differ (73,515 involve marks). Nosifer-Regular (landed CLEAN 7777099): 1,975 of 110,224 (1,968 mark). Example: a+U+0307 is at (530,975) in the release and (1768,0) in ours. KellySlab, Marvel x4, TulpenOne and Wallpoet: 0. See runs/05-kern-only-census/pair_matrix-*.txt. Ultra's 650 A-group pairs would also pass the current rule.
  Upstream: none (this workspace)
- **sfd-reland tools/sfd_edit.py**: Add the op `kernclass0zero <KernClass2 subtable name>`, which zeroes first-class 0's row. It is FATAL without the '+' marker or with a malformed matrix. The file was NOT edited: it has uncommitted changes from another session.

  Evidence: Ultra: 650 -> 0 A-group LTR pair differences (runs/09-ultra-kernclass0).
  Upstream: none (this workspace)

## Families that land once these are in

- varela
- poly

## Decisions for Felipe

- Mechanism for the empty GPOS: a fontc opt-in flag plus a builder3 config key (prototyped, clean, 2 PRs plus a fontc release), or a builder3-only post-compile op (1 PR, not prototyped). Either way nothing lands until it is merged and released, since land.py refuses forks. The PRs are yours to file.
- Reproducing the shell turns HarfBuzz's fallback mark positioning OFF, as the release does, for Varela's 3 and UnifrakturMaguntia's 9 combining marks. Arguably worse rendering, but it is what ships. Dropping sharedLayoutScripts could be a later improvement commit (future_work).
- Smokum and Ultra are not empty-GPOS cases. FontForge exported them with no GPOS, only a legacy kern table, and fontc can only kern through GPOS. Options: accept GPOS kerning with documented HarfBuzz differences (Smokum: 28 soft-hyphen pairs; Ultra: 2211 mark pairs plus 17 soft-hyphen pairs, after the class-0 edit), or hold them. The only exact route is a builder3 op that writes `kern` and drops GPOS. It was not prototyped and is unlikely to be accepted upstream (fontspector flags fonts without GPOS kerning).
- Miama and Nosifer landed CLEAN, but their marks shape differently from the release (73,515 and 1,968 LTR pairs), because the gate's legacy-kern rule does not look at fallback mark positioning. Re-open them, or accept under the same decision as Smokum/Ultra? And should the gate be tightened?
- Ultra's source postdates its release (.sfd saved 2011-10-18, export of the 2011-05-03 state). Should it take the TTFWeight 400 and Weight Regular edits (values from the release/hg binary)? Without the first, land.py's weight workaround opens OS/2.us_weight_class [400,900] (runs/16).
- Does the gate's GDEF.glyph_classes RELEASE-STALE acceptance still fit the 2026-09-24 equivalence rule? Poly-Italic: 1,531 LTR pairs differ because U+0307/U+0326 lose their advance as marks. Varela/UnifrakturMaguntia: vertical text only (28,416 / 45,498 runs).

## Unresolved

- UnifrakturMaguntia-Book keeps 2 rows (hhea.descender, OS/2.us_win_descent): the pre-2014 offset-metrics converter rule from the first batch is still not implemented, so unifraktur does not land from this unit alone.
- Smokum-Regular and Ultra-Regular keep their 3 GPOS rows each pending the kern-only decision. No upstream-plausible tool reproduces a kern-only font.
- Vertical HarfBuzz residue unaffected by the shell: Varela 28,416 runs, UnifrakturMaguntia 45,498. Varela's all involve its 3 marks: the GDEF mark class zeroes their vertical advance. Smokum and UnifrakturMaguntia also have 1-unit vertical-origin (glyf bbox) differences. The gate does not check vertical.
- The GSUB.script_list rows the broad rule would open (33 next-batch styles) show that fontc's kern writer registers scripts (DFLT, grek, cyrl) that FontForge's kern lookup did not. The gate hides this in GPOS ('both fonts position with real lookups'). Not investigated for behaviour.
- Upstream acceptance of the fontc flag is not known: fontc aims at fontmake parity and fontmake has no such option. If refused, the fallback is a builder3 post-compile op.
- Pre-existing, unrelated test failures: fea-rs fonttools_tests cvparam_null.fea (also on the untouched fontc-v1.0.0 tag with local fontTools 4.61.1), and 11 babelfont tests that need the external noto-cjk-varco checkout.
- runs/14-first-batch-off is a partial run (9 of 26 styles, stopped once the narrow rule was chosen); only Kristi and Lekton from it are used.
- Scratch only, disposable or regenerable: prototype clones and targets under /home/fsanches/compartilhado/sfd-reland-scratch/emptygpos/ (fontc-proto, builder3-proto, babelfont-proto, target-*). The patches that matter are copied into the investigation's probes/. Nothing was committed, as instructed.

## Rerun

    cd /home/fsanches/compartilhado/sfd-reland; FAMILIES=families-next.tsv BF=/home/fsanches/compartilhado/babelfont-rs-worktrees/integration-ff-prs/target-heights/release/babelfont OUT=investigations/next-emptygpos/runs/00-baseline TAG=emptygpos-00 SCRATCH=/home/fsanches/compartilhado/sfd-reland-scratch/emptygpos bash tools/baseline.sh Smokum-Regular Ultra-Regular Varela-Regular   (and FAMILIES=families.tsv ... UnifrakturMaguntia-Book)
    B3=/home/fsanches/compartilhado/sfd-reland-scratch/emptygpos/target-b3/release/gftools-builder EXTRA_CONFIG='sharedLayoutScripts: true' FAMILIES=... BF=/home/fsanches/compartilhado/sfd-reland-scratch/emptygpos/target-bf/release/babelfont OUT=investigations/next-emptygpos/runs/10-all-prototypes TAG=emptygpos-10 SCRATCH=/home/fsanches/compartilhado/sfd-reland-scratch/emptygpos bash investigations/next-emptygpos/probes/baseline_b3.sh <Style>
    same without EXTRA_CONFIG and with the pinned BF -> runs/03-proto-flag-off (control); with EXTRA_CONFIG and pinned BF -> runs/04-proto-shared-scripts; tools/baseline.sh with prototype BF -> runs/11-babelfont-proto-only
    $PY investigations/next-emptygpos/probes/ff_shared_scripts.py compare <release.ttf> <built.ttf>
    $PY investigations/next-emptygpos/probes/shape_compare.py <release.ttf> <built.ttf>;  $PY investigations/next-emptygpos/probes/pair_matrix.py <release.ttf> <built.ttf>
    $PY investigations/next-emptygpos/probes/langsys_lookups.py <release.ttf> <built.ttf>;  $PY investigations/next-emptygpos/probes/varela_gsub_check.py <release.ttf> <built.ttf>
    $PY investigations/next-emptygpos/probes/census_layout_shells.py families.tsv families-next.tsv;  $PY investigations/next-emptygpos/probes/recipe_shared_scripts.py families.tsv families-next.tsv
    BUILDS=/home/fsanches/compartilhado/sfd-reland-scratch/baseline TAG=next FAMILIES=families-next.tsv CENSUS=investigations/next-emptygpos/runs/census_layout_shells.tsv OUT=<scratch> bash investigations/next-emptygpos/probes/shared_scripts_sweep.sh
    OLD=<pinned babelfont> NEW=<prototype babelfont> FAMILIES=<tsv> SCRATCH=<scratch> bash investigations/next-emptygpos/probes/fea_diff_sweep.sh
    $PY investigations/next-emptygpos/probes/sfd_kernclass0.py Ultra-TTF.sfd out.sfd "'kern' Horizontal Kerning in Latin lookup 0 kerning class 1"; SRC_OVERRIDE=out.sfd ... bash tools/baseline.sh Ultra-Regular (runs/09); sfd_edit.py setfield TTFWeight 400 / Weight Regular (runs/17, runs/18); RUN=... EDIT=... bash probes/rebuild_glyphs.sh Ultra-Regular (runs/16)
    cd <scratch>/fontc-proto (branch shared-layout-scripts-main): cargo test -p fea-rs --lib -- compile::opts; cargo test -p fontc --bin fontc -- args; cargo clippy -p fea-rs -p fontbe -p fontir -p fontc --all-targets
