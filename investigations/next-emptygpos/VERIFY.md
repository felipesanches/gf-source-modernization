# next-emptygpos -- adversarial verification

**Model**: Claude Opus 5.5. Written from the verifier's structured result.

Reproduced: True

I re-ran every measurement with my own harness runs under /home/fsanches/compartilhado/sfd-reland/investigations/next-emptygpos-verify/runs (scratch: /home/fsanches/compartilhado/sfd-reland-scratch/emptygpos-verify). The pairing is families-next.tsv (and families.tsv for UnifrakturMaguntia), and the releases are google/fonts b5efa9c32e8f.

Pins:
- babelfont integration-ff-prs 17ea899 (sha256 4cbc83e0).
- builder3 e851b8b with fontc 1.0.0.
- table_gate 2f43693.
- uharfbuzz 0.53.3 / HarfBuzz 12.3.2, fontTools 4.61.1.

Everything that follows was reproduced.

- **Baseline (runs/00-baseline):** 17 rows. Smokum 3 GPOS, Ultra 3 GPOS (the build is named Ultra-Black.ttf), Varela 6 (GPOS x3, GSUB x3), UnifrakturMaguntia 5 (GPOS x3, hhea.descender [-513,-514], OS/2.us_win_descent [512,514]).
- **Release layout.** Smokum and Ultra have no GPOS/GSUB/GDEF, only a format-0 `kern` table (3904 and 2721 pairs). The FFTM stamp is 3381227313, which equals v20110222's LibFF_ModTime of 1298382513 (libffstamp.h fetched at tag v20110222). The hg binaries differ from the releases only in head and name (hotfixes 0e5ac906d and 57fc85106). Varela's release is byte-identical to the hg binary.
- **FontForge code, read at v20110222 and at master 67dd7dc9.** The kern condition is at tottf.c:5306 and ttf_dumpkerns calls SFKernClassTempDecompose. That function's class loop starts at i=1 (splinesaveafm.c ~2038). SFScriptsInLookups ignores gpos, SFLangsInScript gives a script with no lookups a dummy DEFAULT_LANG, and dumpg___info keeps a table that has scripts but no lookups. The fea-rs build_raw early return at fontc-v1.0.0 is also as described.
- **LTR pair matrix, my own probe (probes/pairs_hb.py, which does not import sweep.py):**
  - Smokum: 28 of 135,424 pairs differ, all U+00AD-first.
  - Ultra: 2878 of 137,641 (2211 mark, 650 A-group, 17 soft hyphen).
  - Varela: 1532 of 281,961. UnifrakturMaguntia: 2082 of 61,009.
  - Nosifer (fidelity-only baseline): 1,975 of 110,224, of which 1,968 involve marks. This confirms the gate's legacy-kern weakness.
- **Prototypes, rebuilt independently.** I applied the other agent's patch files to fresh scratch clones. The fontc tree is 1134e598, the builder3 tree cc6eaf66 and the babelfont tree 1dc7e1d1, all identical to the agent's prototype trees. My builder3 binary is sha256 4b375fa3..., my babelfont 19274ce0....
  - Flag on (runs/10): Varela goes 6 to 3 (GSUB only), UnifrakturMaguntia 5 to 2. The GPOS script lists equal the release's exactly, and the LTR pair differences drop to 0 for both.
  - Flag off (runs/11): identical to the pinned build except head. This is the control.
  - Prototype babelfont alone (runs/13): Varela has 3 rows (GPOS), Poly-Italic is CLEAN and Poly-Regular stays CLEAN.
  - All prototypes (runs/14): Varela is CLEAN, with the gate's lookup-order arbitration covering 102400 runs, and UnifrakturMaguntia keeps 2 rows. My effect-level GSUB comparison (probes/langsys_effects.py) finds 7 of 161 keys differing at baseline: liga and smcp for AZE/CRT/TRK, plus aalt for latn/SRB. With all prototypes it finds 0 of 160. The cited cases (fi under tr/az/crh, aalt '!' under sr) behave as claimed (runs/14/lang_cases.txt).
  - Kristi and Lekton-Regular with the flag (runs/12): CLEAN, with the release's exact GPOS shell.
- **Census (probes/shell_census.py):** 5 empty-GPOS shells, 76 empty-GSUB shells and 11 legacy-kern-only releases.

Not re-run: the fontc and babelfont unit tests and clippy, Lekton-Bold, the 81-style broad-rule sweep, and the 149-style FEA regression screen.

One provenance problem with the other agent's evidence. Their builder3 prototype (734e373e) was built at 01:44:18, but the fontc commit 0df9f5ee dates from 02:28:19. So runs/04, 10 and 15 came from an uncommitted fontc working tree. My rebuild from the committed patch gives the same results, so the evidence stands, but the binary pin in their result should point at a build from the committed patch.

## Verdict

The investigation holds up for Varela, UnifrakturMaguntia and Smokum, but not for Ultra.

For Varela and UnifrakturMaguntia, the causes are right: FontForge's shared GSUB/GPOS script list, a fea-rs gap, and babelfont's include_dflt and aalt registration. I rebuilt the fontc/builder3 and babelfont prototypes from the patch files and they reproduce every claimed outcome. Varela is CLEAN with all prototypes, UnifrakturMaguntia keeps only its 2 first-batch vmetric rows, Poly is CLEAN, Kristi and Lekton-Regular are CLEAN with the exact shell, and horizontal pair differences go to 0. Two things need fixing before any PR is filed:
- The fontc patch text wrongly says HarfBuzz ignores a legacy `kern` table whenever a GPOS exists.
- The builder3 key is silently ignored by current builder3 and rejected by the Python builder, so landing and verification must check the built shell.

Smokum is correctly identified as a kern-only release, and its U+00AD analysis is right.

Ultra is where the result is wrong. The three proposed .sfd edits (TTFWeight 400, Weight Regular, kernclass0zero) should be rejected. The release was exported from googlefontdirectory-hg 2d042ebbd's Ultra-TTF.sfd, an exact FFTM ModificationTime match, and that file needs no edit at all: weight 400, Weight Book with correct Regular names, per-glyph kerning with no A-group, and .null/nonmarkingreturn present. The pairing uses the October 2011 re-save instead, and the A-group kerning was added in that re-save, not dropped by FontForge. What remains for Ultra is the same decision as Smokum (GPOS kerning versus a legacy-kern release): 2211 mark pairs and 17 soft-hyphen pairs.

landable_after: varela and poly, once the babelfont PR merges; varela additionally needs the fontc release and builder3 PR. unifraktur still needs the vmetric rule. smokum, and ultra re-paired to 2d042ebbd, need Felipe's kern-only decision.

Nothing was committed. Probes and runs are in /home/fsanches/compartilhado/sfd-reland/investigations/next-emptygpos-verify/{probes,runs}. The scratch clones and targets under /home/fsanches/compartilhado/sfd-reland-scratch/emptygpos-verify are disposable: they rebuild from the patch files in next-emptygpos/probes.

## Per edit

- [reject] Set TTFWeight to 400, the weight class Ultra was released with -- The value is right but the origin is wrong, and the edit is not needed. The .sfd the release was actually exported from is in version control: googlefontdirectory-hg 2d042ebbd:ultra/src/Ultra-TTF.sfd (old-branch layout, 'Updating Ultra', 2011-05-06). Its ModificationTime is 1304463351, which equals the release's FFTM sourceModified; the next-provenance probe fftm_source_commit.py reports MATCH at 2d042ebbd. That file says TTFWeight: 400. The hg ultra/Ultra.ttf at 2d042ebbd has the same blob (11a5d859) as apache/ultra/Ultra.ttf at 52f780bc and as google/fonts 90abd17b4:apache/ultra/Ultra.ttf. The pairing's .sfd is the 2011-10-17 re-save ('Updating hinting of Ultra', 10ef7b362), whose binary never shipped. Pair Ultra with the 2d042ebbd .sfd instead of copying the value from the binary. Built unmodified from it, the weight is 400 with no row (runs/02-ultra-may-sfd).
- [reject] Set Weight to Regular, as the released Ultra is named -- The value never existed in the source's history. The exported .sfd (2d042ebbd) says `Weight: Book`, not Regular; the value was taken from the binary's nameID 2. Built unmodified from the 2d042ebbd .sfd, babelfont already produces Ultra-Regular.ttf with nameID 1/2/4/6 = Ultra / Regular / Ultra Regular / Ultra-Regular, matching the hotfixed release (runs/02-ultra-may-sfd). With the correct pairing no name edit is needed.
- [reject] Drop kerning class 0's row, as the released kern table has no A-group pairs -- The cause is wrong. The commit body says FontForge's legacy-kern writer dropped class 0. That code is real (splinesaveafm.c i=1), but it did not act here: the .sfd exported on 2011-05-03 (2d042ebbd) has no KernClass2 at all. It has 110 per-glyph Kerns2 lists and none on an A-group glyph (runs/02-ultra-may-sfd/sfd_history.txt). The A row arrived with the October 2011 re-save, which restructured the kerning into KernClass2 '26+ 27', removed .null and nonmarkingreturn, and set Weight Black / TTFWeight 900. That is later design history, not an exporter artefact. Built from the exported .sfd with no edit, the A-group differences are 0 and the total is 2228 LTR pairs (2211 mark + 17 soft hyphen). That is the same end state as the three edits, and the post.num_glyphs RELEASE-STALE row also disappears. The new sfd_edit op is unnecessary.

## Per tool change

- [revise] fontc (fea-rs Opts::share_script_lists + Flags::SHARED_LAYOUT_SCRIPTS + --shared-layout-scripts) -- The mechanism is correct and I reproduced it from the committed patch (tree 1134e598): Varela 6->3, UnifrakturMaguntia 5->2, Kristi and Lekton-Regular CLEAN. The shell equals the release's GPOS script list, LTR pair differences go to 0, and the flag-off control differs only in head. Revise before filing, because the upstream-facing text states a false HarfBuzz behaviour. The opts.rs doc comment says HarfBuzz 'does not apply its fallback mark positioning or a legacy `kern` table to a font that has a GPOS table', and the commit message repeats it. hb-ot-shape.cc at 12.3.2 (lines 134, 173) applies the legacy `kern` table whenever GPOS has no `kern` feature (`!has_gpos_kern || !plan.apply_gpos`). Only fallback mark positioning (and fallback kern) is switched off by an empty GPOS. Also re-pin the evidence to a builder3 built from the committed fontc patch: 734e373e predates commit 0df9f5ee by 44 minutes. Upstream acceptance is still unknown, since fontc tracks fontmake parity.
- [revise] gftools-builder3 FontcConfig sharedLayoutScripts -- The patch is fine (tree cc6eaf66; built as 4b375fa3 and it works). One point the other agent did not report: FontcConfig and GoogleFontsOptions do not deny unknown fields. So on any builder3 before this change, including the prebuilt main-latest binary the landed repos' CI downloads (.github/workflows/build.yaml), `sharedLayoutScripts: true` is silently ignored and the font is built without the shell, with no error. Separately, the Python gftools builder's GOOGLEFONTS_SCHEMA rejects the key ('unexpected key not in schema', tested with the local gftools 0.9.100.dev). The landing and verification must therefore check the built GPOS shell, not trust the key, and must refuse builder3 revisions that lack the change.
- [keep] babelfont-rs make_langsys exclude_dflt for non-dflt languages -- This is a correct fidelity fix: FontForge registers each lookup for exactly the languages it names. The patch was reproduced (tree 1dc7e1d1). With both babelfont commits, Varela's GSUB effects go from 7 of 161 differing keys to 0 of 160, fi does not ligate under tr/az/crh, and Poly-Italic and Poly-Regular are CLEAN. The PROTOTYPE commit author/subject ('scratch <scratch@localhost>') needs replacing before the PR.
- [keep] babelfont-rs declare only aalt's languagesystems when there is no kerning and no anchors -- It works. Reproduced: Varela GSUB 3->0 together with exclude_dflt, aalt no longer under latn/SRB ('!' stays exclam under sr), Poly-Italic 3->0 and Poly-Regular still CLEAN. It is the only FEA-expressible route, because aalt forbids script/language statements. It is a conditional heuristic that falls back to a warning when kerning or anchors exist, so upstream acceptance is medium. The PR text should say plainly that it relies on explicit `script`/`language` statements for undeclared language systems, which fea-rs accepts.
- [revise] sfd-reland recipe/baseline/land: sharedLayoutScripts for FFTM + empty GPOS + GSUB with lookups (narrow rule) -- The rule selects exactly the 5 empty-GPOS releases (my independent census agrees), and Kristi and Lekton-Regular stay CLEAN with the exact shell (runs/12). Because builder3 silently ignores the key, verify_landed.py and land.py must assert that the built font has the GPOS or GSUB shell and must pin a builder3 that has the change. Otherwise a CI or rebuild on current builder3 produces a font without the shell and nothing notices.
- [keep] table_gate arbitrate_legacy_kern: account for fallback mark positioning and shape the full pair matrix -- The code (table_gate.py 1250-1313 at 2f43693) shapes only the release's own kern pairs and compares advance sums, so mark fallback differences are invisible to it. I reproduced Nosifer's fidelity-only build: 1,975 of 110,224 LTR pairs differ, 1,968 of them involving marks.
- [reject] sfd-reland tools/sfd_edit.py kernclass0zero op -- It is not needed. The A-group row it removes is not in the .sfd Ultra was exported from (2d042ebbd). Fix the pairing instead.

## Objections

- Ultra-Regular GPOS.script_list/feature_list/lookup_list: keeping these as 'decision' (kern-only release) is right, but the cause text is wrong in two places. The A-group kerning (650 pairs) is attributed to FontForge's class-0 decompose rule, but the exported .sfd had no kern classes. The source is described as postdating the export, as if the exported state were unknown, but it is in googlefontdirectory-hg history at 2d042ebbd. With the correct source, the functional residue is 2211 mark pairs plus 17 soft-hyphen pairs, and there is no weight, name or glyph-count issue.
- Varela-Regular and UnifrakturMaguntia-Book GPOS rows are classified 'compiler-gap' here. The first batch classified UnifrakturMaguntia's same three rows as 'converter-fidelity' (investigations/unifraktur/FINDINGS.md). Same mechanism, same rows: pick one label for both batches. 'compiler-gap' is the more accurate one, since babelfont and FEA cannot express the shell.
- Varela GSUB rows: the 'converter-fidelity' label and the cause are right. The count '16 of 161 keys' is a lookup-index count that includes packing and ordering. Measured by effect, 7 of 161 keys differ (AZE/CRT/TRK liga and smcp, latn/SRB aalt; runs/03-varela-gsub). The substance is the same.

## Missed

- The Ultra pairing is wrong at the revision level, which is the main finding. families-next.tsv pairs Ultra-Regular with googlefontdirectory-hg 52f780bc apache/ultra/src/Ultra-TTF.sfd, the 2011-10-17 re-save (blob 3b258c0a, same as 10ef7b362 'Updating hinting of Ultra'). The release was exported from 2d042ebbd:ultra/src/Ultra-TTF.sfd (blob 78bfdba4, ModificationTime 1304463351 == FFTM sourceModified; its Ultra.ttf blob 11a5d859 is the one google/fonts shipped). Built unmodified with the pinned fidelity flags, it gives only the 3 kern-only GPOS rows and 0 stale rows (runs/02-ultra-may-sfd; recipe probes/ultra_exported_sfd.sh). The harness and land.py cannot take this yet: they do `git archive <commit> <lic>/<fam>` with --strip-components=2, but at 2d042ebbd the path is `ultra/`, strip 1. A pairing and harness change is needed, or a Felipe decision on the repository history: May .sfd as the base, the convert commit, then the October .sfd as a later future-work commit.
- The same FFTM-vs-.sfd check across both pairing tables (probes/fftm_vs_sfd.py, runs/06-fftm-vs-sfd.txt) flags the paired .sfd as newer than the release for Ultra-Regular, Lohit-Bengali, Lohit-Tamil, Thabit, Thabit-Bold and Piedra-Regular (Piedra by only 17 s). next-provenance covers Lohit and Thabit. Ultra was covered by no unit.
- The HarfBuzz statement in the fontc patch's doc comment and commit message is false (see the tool verdict), and it would be the first thing an upstream reviewer checks.
- builder3 silently ignores unknown config keys, and the Python gftools builder rejects `sharedLayoutScripts`. The recipe's config key is therefore not self-enforcing.
- The builder3 prototype binary (734e373e) used for runs/04, 10 and 15 was built 44 minutes before fontc commit 0df9f5ee existed, so it came from an uncommitted working tree. Results reproduce from the committed patch (my build 4b375fa3), so only the pin in the verification section is wrong.
