# next-gsub -- investigation findings

**Model**: Claude Opus 5.5 (investigating agent, adversarial verifier, and the
conclusion below). Written from the agents' structured results (`results.json`).

## Conclusion

Megrim was exported with OpenType off (like Nosifer): three documented droplookup edits.
Poly-Italic and Varela need the two babelfont language-system fixes shared with the
empty-GPOS unit. RibeyeMarrow is functionally equal and blocked only by the table gate's
contextual-lookup comparison (a gate fix).

## Investigator's report

All four styles were rebuilt through the pipeline's own pairing (families-next.tsv).
Sources are hg 52f780bc (Megrim-TTF.sfd a1942e6c, Poly-Italic-TTF.sfd d73eef79,
RibeyeMarrow-Regular-TTF.sfd f3bf8aab, Varela-Regular-TTF.sfd e5f628c1). Releases are
google/fonts b5efa9c3, byte-identical to the hg blobs. All four releases carry the
FontForge 20110222 FFTM stamp, and each FFTM source time equals its .sfd's times. r0
reproduces baseline-next exactly. Each difference was named with gsub_semantic_diff and
checked for function with uharfbuzz over the cmap (shape_compare, with feature-firing
counts and advance-only runs separated out). Candidates: r1 Megrim droplookups
(integration converter 17ea899); r2 prototype converter (17ea899 + language-systems
diff, built in scratch); r3 prototype + Megrim edit; r4 prototype + edits + land.py
workarounds under both gates; r5 first-batch regression of the converter change. The
gate change was checked with a 106-style sweep and with negative tests.

Rows before: Megrim BLOCKING 4 (GSUB.feature_list, GSUB.lookup_list, GSUB.script_list, OS/2.us_weight_class). Poly-Italic BLOCKING 3 (GSUB x3). RibeyeMarrow-Regular BLOCKING 2 (GSUB.feature_list, GSUB.lookup_list). Varela-Regular BLOCKING 6 (GPOS x3, GSUB x3). Source: runs/r0-unmodified, identical to baseline-next.tsv.

Rows after: Megrim CLEAN 0 (3 droplookup edits + weight workaround; shared and proposed gate). Poly-Italic CLEAN 0 (babelfont prototype; shared gate). RibeyeMarrow-Regular CLEAN 0 (proposed gate; the shared gate still gives 2). Varela-Regular BLOCKING 3, GPOS.* only: all GSUB rows closed, GPOS belongs to the empty-GPOS unit. Source: runs/r4-final-shared-gate and runs/r4-final-proposed-gate.

Confidence: High. Every row's cause is reproduced from the source under the pipeline's own pairing. The releases carry exactly the .sfd's lookup order and registrations (58/58 lookups). Each fix is harness-verified (rows before -> after), and every functional claim rests on uharfbuzz runs with feature-firing counts. Megrim's non-OpenType export rests on the table set, the FFTM/.sfd timestamps, FontForge v20110222 initATTables and the same-session Jura exports, as Nosifer's did. The gate change is verified by a 106-style sweep and by measured negative tests. Its first-batch coverage is missing.

## Rows

| style | row | class | cause |
|---|---|---|---|
| Megrim | OS/2.us_weight_class [500, 400] | compiler-gap | fontc 1.0.0 ignores a single-master Glyphs source's instance weightClass and writes 400. The .sfd states TTFWeight: 500 (line 25), and the release carries 500. This is the known gap (issues/fontc-static-weight-class.md), already closed by land.py's weight-class workaround (tools/workarounds.py), which writes the value as FEA from the .sfd. |
| Megrim | GSUB.script_list [null, {DFLT/dflt, latn/dflt, latn/TRK}] | source-edit-from-release | FontForge 20110222 exported Megrim.ttf with OpenType output OFF, as it did Nosifer. The source declares 3 GSUB lookups (.sfd lines 56-58: aalt latn/dflt, ss01 DFLT+latn dflt, locl latn/TRK). The release has no GSUB, GPOS, GDEF or DSIG, usMaxContext is 1, and the ss01/i.TRK glyphs ship unreachable. In v20110222 tottf.c initATTables, GSUB/GPOS/GDEF are written only in opentypemode. The .sfd does not record the export mode, so the absence exists only in the release. |
| Megrim | GSUB.feature_list [null, {aalt, locl, ss01}] | source-edit-from-release | Same cause: the release was exported with FontForge's OpenType tables off, so aalt/ss01/locl were never written. |
| Megrim | GSUB.lookup_list [null, {0: aalt single, 1: ss01 single, 2: locl i->i.TRK}] | source-edit-from-release | Same cause. The lookups exist only in the source. The release ships their target glyphs (M.ss01 ... y.ss01, i.TRK) unreachable. |
| Poly-Italic | GSUB.script_list {latn/ROM: aalt added} | converter-fidelity | The .sfd registers aalt (lines 57-58, lookups 0 and 1) for ('latn' <'dflt'>) only. babelfont writes aalt's rules directly into `feature aalt`, because no script or language statement is legal there. fea-rs 1.0.0 registers aalt for EVERY `languagesystem` (compile/features.rs finalize_aalt: 'add the aalt feature to all the default language systems'; compile_ctx.rs resolve_aalt_feature reads only Gsub1/Gsub3/feature refs). `languagesystem latn ROM` is declared for locl/zero (lines 60-61), so our build registers aalt under latn/ROM and the release does not. |
| Poly-Italic | GSUB.feature_list (case/dnom/frac/lnum/... indices shifted by one) | gate-arbitration | babelfont defines lookups in .sfd order with one documented deviation (fontforge.rs: 'a dependency declared after its caller is hoisted to just before it'). A feature file must define a lookup before a chain rule names it, so the feature-less lookup 18 (.sfd line 75, reached only from frac lookup 7) becomes index 7 and every later index moves up by one. This cannot be expressed otherwise in FEA. It has no shaping effect because the hoisted lookup is applied only through the chain. |
| Poly-Italic | GSUB.lookup_list (index 7: chain vs single) | gate-arbitration | Same hoisted nested lookup 18. Lookup contents are identical, and the only difference is the position of a lookup that no feature references. |
| RibeyeMarrow-Regular | GSUB.feature_list {frac: [4, 7], ordn: [3, 4]} | gate-arbitration | The feature-less lookups 5, 6 and 7 (.sfd lines 61-63), called only from ordn (lookup 3) and frac (lookup 4), are hoisted before their callers, as babelfont's documented FEA-ordering deviation does. The indices shift, and the application order of feature lookups is unchanged. |
| RibeyeMarrow-Regular | GSUB.lookup_list {3: chained_sequence_context vs single; frac type 6 vs 5} | gate-arbitration | The hoisting above, plus a compiler representation choice. frac (.sfd line 60, nine ChainSub2 subtables at lines 160-231, none with backtrack or lookahead) is compiled by fea-rs 1.0.0 as ONE type-5 SequenceContext subtable (compile/lookups/contextual.rs into_lookups: Chain only if some rule has backtrack/lookahead). FontForge wrote nine type-6 format-3 subtables. The nine rules are the same, in the same order per first glyph (0/00 before 0/0). A type-6 rule with no backtrack or lookahead is a type-5 rule. The shared gate refuses at condition 2 on the lookup type alone (GATE_TRACE 'rules differ; types False') and never shapes. |
| Varela-Regular | GSUB.script_list (latn/AZE, CRT, TRK liga + smcp; latn/SRB aalt) | converter-fidelity | There are two converter causes, and the release registers exactly what the .sfd states (31/31). (a) babelfont writes `language AZE;` etc. In a feature file that INCLUDES the default language's lookups for the feature (include_dflt), while FontForge registers a lookup only for the languages it names. So liga lookup 24 (line 81: DEU MOL ROM SRB dflt, deliberately not AZE/CRT/TRK) and smcp lookup 21 (line 78) also run under AZE/CRT/TRK. (b) aalt (lines 57-58, no SRB) is registered for latn/SRB, because SRB is declared for liga/dlig and fea-rs registers aalt for every languagesystem. |
| Varela-Regular | GSUB.feature_list (c2sc/dlig/dnom/frac/... indices shifted) | gate-arbitration | The nested-only lookups 28-30 (lines 85-87) are hoisted to 8-10 before their callers (frac 8, ordn 12), so every later index shifts. There is no shaping effect. |
| Varela-Regular | GSUB.lookup_list (8: chain vs ligature; ordn 4 vs 2 subtables) | gate-arbitration | The hoisting above, plus fea-rs packing. ordn (line 69) has four FontForge ChainSub2 subtables (lines 90-118: digits a', digits o', digits period a', digits period o'). fea-rs writes them as 2 format-3 subtables with input coverage [a o], merging rules that differ only in the input glyph. The rules per first glyph and their order are identical. The shared gate accepts this only because it never compares contextual rules. The proposed gate accepts it on rule equality. |
| Varela-Regular | GPOS.script_list / GPOS.feature_list / GPOS.lookup_list | compiler-gap | This row is outside this unit (empty-GPOS unit). FontForge gives GSUB and GPOS the same script list and writes an empty GPOS shell (cyrl/grek/latn, no lookups); fontc omits the table. Its presence suppresses HarfBuzz fallback mark positioning. |

## Proposed .sfd edits

- **Drop the aalt lookup the release does not carry** (Megrim) `droplookup 'aalt' Access All Alternates in Latin lookup 0` -- verified: True; value from: The release's table set (no GSUB/GPOS/GDEF/DSIG, usMaxContext 1) read against FontForge v20110222 tottf.c initATTables, which writes layout tables only in opentypemode. The release's FFTM source-modified time equals the .sfd's ModificationTime (2011-04-28 15:00:19). The Jura TTFs exported 93-107 s later in the same session also lack GSUB/GPOS although their sources declare lookups. No value is taken from the binary: the edit only removes what the source declares.; the source stated: Line 56: Lookup: 1 0 0 "'aalt' Access All Alternates in Latin lookup 0" ... ['aalt' ('latn' <'dflt' > ) ], plus 11 Substitution2 glyph entries (M N R U V W Y i m w y). The edit removes exactly these 12 lines.
- **Drop the ss01 lookup the release does not carry** (Megrim) `droplookup 'ss01' Style Set 1 lookup 1` -- verified: True; value from: Same evidence as the aalt edit (release table set + v20110222 initATTables + FFTM/.sfd timestamps + the 2011-05-03 Jura batch).; the source stated: Line 57: Lookup: 1 0 0 "'ss01' Style Set 1 lookup 1" ... ['ss01' ('    ' <'dflt' > 'latn' <'dflt' > ) ], plus 10 Substitution2 entries (M N R U V W Y m w y; note that the source maps capital Y to y.ss01). The edit removes exactly these 11 lines.
- **Drop the Turkish locl lookup the release does not carry** (Megrim) `droplookup 'locl' Localized Forms in Latin lookup 2` -- verified: True; value from: Same evidence as the aalt edit.; the source stated: Line 58: Lookup: 1 0 0 "'locl' Localized Forms in Latin lookup 2" ... ['locl' ('latn' <'TRK ' > ) ], plus 1 Substitution2 entry (i -> i.TRK). The edit removes these 2 lines. All three edits applied in this order give edits/Megrim.droplookups.sfd. Verified together: runs/r1-megrim-droplookups 4 -> 1 (us_weight_class), and with land.py's weight workaround CLEAN 0 (runs/r1w, runs/r4-final-shared-gate, runs/r4-final-proposed-gate).

## Proposed tool changes

- **babelfont-rs (FontForge convertor, layout.rs make_langsys)**: Write `language XXX exclude_dflt;` for every language other than dflt. A FontForge lookup runs only for the (script, language) pairs it names, while a feature-file `language` statement inherits the default language's lookups for that feature unless it says exclude_dflt.

  Evidence: The releases carry exactly the .sfd's registrations (runs/sfd_vs_release_registration.txt: Poly-Italic 19/19, RibeyeMarrow 8/8, Varela 31/31). Varela r0: liga lookup 24 is inherited under AZE/CRT/TRK, so Turkish/Azeri/Crimean Tatar 'fi' and 'ffi' ligate in our build and not in the release (runs/shape/Varela-Regular.r0.txt). With the change: 0 of 33,388,586 runs differ (r2). Regression: the 9 first-batch styles whose FEA changes (Lekton x2, PatrickHand, Play, Tuffy x2, AbrilFatface, ComicRelief x2) keep identical gate rows (runs/r5-first-batch-regression). The emptygpos FEA sweep (next-emptygpos/runs/12-babelfont-regression) shows no other next-batch style changes. Converter tests: fontforge tests 80 -> 82 all pass. The same 11 unrelated tests fail on base and prototype because they read ../noto-cjk-varco fixtures (runs/converter_tests.txt).
  Upstream: yes: simoncozens/babelfont-rs, one PR together with the aalt change and shared with the empty-GPOS unit (Felipe files it; no GitHub write access here). Landing cites it only after it merges.
- **babelfont-rs (FontForge convertor, fontforge.rs languagesystem emission)**: When aalt is registered for fewer language systems than the other lookups, and the compiler will generate no feature from kerning or anchors, declare only aalt's language systems. fea-rs registers aalt for every `languagesystem` and allows no script/language statement inside it. Every other FontForge lookup is written with explicit script/language statements, so those are unaffected. Otherwise the converter keeps all declarations and logs a warning.

  Evidence: fea-rs 1.0.0 compile/features.rs finalize_aalt ('add the aalt feature to all the default language systems') and compile_ctx.rs resolve_aalt_feature. Poly-Italic r0: aalt under latn/ROM changes 1380 of 2331 Romanian aalt runs. With the change, Poly-Italic is CLEAN 0 with the shared gate (runs/r2-bf-langsys, runs/r4-final-shared-gate), Poly-Regular stays CLEAN 0, and the Varela latn/SRB aalt key disappears (semdiff r2: 160 keys). Megrim's FEA also changes (DFLT no longer declared), but its GSUB is dropped by the edits anyway (r3 -> r4 CLEAN).
  Upstream: yes: the same babelfont-rs PR as exclude_dflt. It is a heuristic (conditional on no kerning/anchors), so Simon may want another design.
- **table gate (sfd-batch5/tools/table_gate.py arbitrate_gsub_lookup_order; our measurement tool, not a font-build tool)**: Compare CONTEXTUAL lookups by their rules: for every glyph that can start a match, the ordered rules (backtrack/input/lookahead glyph sets, nested lookups by content), so lookup type 5 vs 6, format and subtable packing count as representation. Also shape every sequence a contextual rule or ligature spells, besides the 2-character corpus, and state a type/packing difference in the RELEASE-STALE line. The shared gate treats every contextual lookup as (type, 0 entries), so it never compared their rules. That made it both too strict (type 5 vs 6) and too loose (rule changes a 2-character corpus cannot reach).

  Evidence: RibeyeMarrow-Regular goes 2 -> 0 (runs/r4-final-proposed-gate). Sweep over 106 complete next-batch harness runs: RibeyeMarrow-Regular is the only verdict that changes, and no row opens anywhere (runs/gate_sweep_next.tsv). Negative tests (runs/gate_ctx_negative.*.txt), with behaviour measured by shaping: the shared gate ACCEPTS 3 behaviour-changing mutations (Varela ordn drop-last '0.a', ordn retarget '0a', frac drop-last '0/1') and FALSE-BLOCKS the correct RibeyeMarrow build. The proposed gate refuses every behaviour-changing mutation and accepts both correct builds. It is conservative (refuses) on 4 behaviour-neutral mutations.
  Upstream: no: sfd-batch5 is our repository. Felipe must approve folding it into table_gate.py and commit it.

## Families that land once these are in

- megrim (3 droplookup edits + existing weight-class workaround; CLEAN 0 with either gate)
- poly (Poly-Italic with the babelfont language-systems change, CLEAN 0 with the shared gate; Poly-Regular already CLEAN)
- ribeyemarrow (with the gate change alone, on the current converter or the prototype)
- varela (GSUB closed by the babelfont change; the family lands CLEAN only together with the empty-GPOS unit's fontc/builder3 GPOS-shell change)

## Decisions for Felipe

- Megrim: reproduce the release by dropping the aalt, ss01 and locl lookups (the Nosifer precedent; restoring them is future work, done by reverting the three commits), or keep them as better than the release (the build then does not reproduce it). If they are restored later: the source's ss01 maps capital Y to y.ss01.
- File the babelfont-rs PR with the two language-system commits (exclude_dflt; aalt language systems). It is shared with the empty-GPOS unit. land.py can cite it only after it merges upstream.
- Is the conditional aalt fix acceptable? It applies only when no kerning or anchors make fontc generate features. Otherwise it warns and keeps the extra aalt registrations. The alternative is to ask Simon for a general design.
- Approve replacing arbitrate_gsub_lookup_order in sfd-batch5/tools/table_gate.py with the proposed version (stricter on contextual rules, conservative on neutral reorders). Without it, RibeyeMarrow-Regular needs a documented exception to land.

## Unresolved

- Varela-Regular's 3 GPOS rows belong to the empty-GPOS unit, and the family lands only with that change.
- The aalt fix does not cover a font whose aalt is narrower than its other registrations and which has kerning or anchors: fontc registers kern/mark for every declared language system. No style in this unit hits it (RibeyeMarrow has kerning, but its aalt covers all its language systems).
- Hoisted nested lookups cannot be ordered as FontForge did in FEA. They are accepted as representation only because every hoisted lookup here is feature-less (Poly 18; RibeyeMarrow 5-7; Varela 28-30). If a hoisted lookup were also feature-registered, the application order would change.
- The proposed gate was swept over the 106 complete next-batch runs only. Cardo-Regular had no complete run, and the first batch's harness runs no longer exist in scratch. Because it is conservative on neutral reorders of disjoint rules, it could false-block a future style.
- Converter test suite: 11 tests fail identically on base 17ea899 and on the prototype because they read ../noto-cjk-varco fixtures that a clean checkout lacks. This is pre-existing and environment-dependent, not caused by the change (runs/converter_tests.txt).
- Megrim builds as Megrim-Medium.ttf (the .sfd subfamily is 'Medium'); the release file is Megrim.ttf. This is not a table row; file naming at landing is outside this unit.
- The Varela release's Turkish/Azeri/Crimean Tatar small-cap i gives i.smcp, not idotaccent.smcp, because lookup 22 precedes 23 in the .sfd. It is reproduced as fidelity; the fix is future work.

## Rerun

    cd /home/fsanches/compartilhado/sfd-reland; I=$PWD/investigations/next-gsub; PY=/home/fsanches/compartilhado/gftools/venv/bin/python3; SC=/home/fsanches/compartilhado/sfd-reland-scratch/gsub; BFI=/home/fsanches/compartilhado/babelfont-rs-worktrees/integration-ff-prs/target-heights/release/babelfont; BFP=$SC/bf-target/release/babelfont
    for s in Megrim Poly-Italic RibeyeMarrow-Regular Varela-Regular; do FAMILIES=$PWD/families-next.tsv BF=$BFI OUT=$I/runs/r0-unmodified TAG=gsub-r0 SCRATCH=$SC bash tools/baseline.sh $s; done
    FAMILIES=$PWD/families-next.tsv BF=$BFI OUT=$I/runs/r1-megrim-droplookups TAG=gsub-r1 SCRATCH=$SC SRC_OVERRIDE=$I/edits/Megrim.droplookups.sfd bash tools/baseline.sh Megrim
    git clone /home/fsanches/compartilhado/babelfont-rs $SC/bf-src; git -C $SC/bf-src checkout 17ea899; git -C $SC/bf-src apply $I/probes/babelfont-17ea899-langsys-as-built.diff; sudo -n /usr/local/sbin/drop-caches; (cd $SC/bf-src && CARGO_BUILD_JOBS=3 CARGO_TARGET_DIR=$SC/bf-target cargo build --release -p babelfont --features cli)
    for s in Poly-Italic Poly-Regular Varela-Regular RibeyeMarrow-Regular Megrim; do FAMILIES=$PWD/families-next.tsv BF=$BFP OUT=$I/runs/r2-bf-langsys TAG=gsub-r2 SCRATCH=$SC bash tools/baseline.sh $s; done
    FAMILIES=$PWD/families-next.tsv BF=$BFP OUT=$I/runs/r3-bf-langsys+megrim-droplookups TAG=gsub-r3 SCRATCH=$SC SRC_OVERRIDE=$I/edits/Megrim.droplookups.sfd bash tools/baseline.sh Megrim
    RUN=$SC/baseline/<Style>-gsub-r2 (Megrim: -gsub-r3) SRC=<the converted .sfd> OUT=$I/runs/r4-final-{shared,proposed}-gate TG=<shared table_gate.py | $I/probes/table_gate_gsub_proposed.py> bash $I/probes/regate.sh <Style>
    $PY $I/probes/gsub_semantic_diff.py <release.ttf> <build.ttf>; $PY $I/probes/shape_compare.py <release.ttf> <build.ttf>; $PY $I/probes/sfd_vs_release_registration.py <file.sfd> <release.ttf>
    $PY $I/probes/release_export_mode.py Megrim Poly-Italic RibeyeMarrow-Regular Varela-Regular --batch
    bash $I/probes/gate_sweep.sh > $I/runs/gate_sweep_next.tsv
    $PY $I/probes/gate_ctx_negative.py <release.ttf> <accepted-build.ttf> <scratch> <ordn|frac>
    for s in Lekton-Bold Lekton-Regular PatrickHand-Regular Play-Regular Tuffy-Italic Tuffy-Regular AbrilFatface-Regular ComicRelief-Regular ComicRelief-Bold; do FAMILIES=$PWD/families.tsv BF=$BFI|$BFP OUT=$I/runs/r5-first-batch-regression/{integration,proto} TAG=gsub-r5-{integration,proto} SCRATCH=$SC bash tools/baseline.sh $s; done
