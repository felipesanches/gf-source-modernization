# heights -- adversarial verification

**Model**: Claude Opus 5.5. Written from the verifier's structured result.

Reproduced: True

I reproduced the results exactly. I did not reuse their edited files. I started from the unmodified sources (git -C .../googlefontdirectory-hg.git show 52f780bc:ofl/<fam>/src/<X>-TTF.sfd, byte-identical to the archived tree) and inserted the header lines with my own script after FontName:. My copies came out byte-identical to their edits/*.sfd, and each differs from its source only by the one or two added lines. I ran tools/baseline.sh one build at a time (TAG=heights-verify, SCRATCH and OUT under scratchpad/inv-heights-verify/).
Converter ca43adc (target-heights, BUILT_FROM ca43adc491fa) plus my edits:
- HerrVonMuellerhoff: 0 blocking, 6 stale.
- Miama: 0 blocking, 1 stale.
- NosiferCaps: 1 blocking (us_weight_class [800,400]), 16 stale.
- PatrickHand: 0 blocking, 45 stale.
- UnifrakturCook: 1 blocking (us_weight_class [700,400]), 22 stale.
Converter ca43adc on the unmodified sources: HerrVonMuellerhoff cap [644,761]; Miama sx [265,498]; NosiferCaps wc, sx [925,1387], cap [854,1388]; PatrickHand cap [661,660]; UnifrakturCook wc, sx [319,1087], cap [485,1577].
Pinned f725e6a plus the PatrickHand edit: only sx [467,500] is left, and apart from the cap row that gate is identical to the unedited pinned gate.
Every gate printed its closing 'N blocking table difference(s)' line. Each of my gates is byte-identical to the matching gate in their runs/. With the height rows removed, each after-gate is identical to its before-gate. Their before-f725e6a gates match baseline/ except for the order on the flags line.
Independent rule check: I wrote scratchpad/inv-heights-verify/indep_heights.py (sha256 a0d7179ea2e8fd36...). It measures the RELEASE binaries' glyf (or CFF) outlines through fontTools with exact arithmetic, a separate data path from the .sfd parsers. Its per-glyph tops match their .sfd dumps for all 44/80/44/47/43 list glyphs. The one exception is UnifrakturCook L, S and V, where the .sfd has fractional coordinates that the export rounded (L 1535.883 -> 1536). That changes the cap sum from 12617.264 to 12618.018 and gives the same 485 and 1577.
Integer results from the release outlines:
- HerrVonMuellerhoff: x flat mode 269 (flats 264x1, 269x2, 278x1). Cap 16758/26 = 644 under the 2011 divisor; 761 under 2012.
- Miama: x 7968/30 = 265 vs 7968/16 = 498. Cap is the mean of the tied flats 890 and 898 = 894.
- NosiferCaps and Nosifer: x 16652/18 = 925 vs 1387; cap 22211/26 = 854 vs 1388.
- UnifrakturCook: x 5436/17 = 319 vs 1087; cap 485 vs 1577.
- PatrickHand release: x 467.64, cap 660.42 (not 661).
- PatrickHand-Regular.otf (cubic CFF): x 467.505, cap 9921.728/15 = 661.449, so 661.
The oracle (tools/ff_heights_oracle.py families.tsv) gives HerrVonMuellerhoff 269/761, so the brief's 271 is wrong. It also gives Miama cap 894, so the brief's 898 is wrong as well; they did not flag that one.

## Verdict

Their findings hold up. I reproduced every row count exactly. The root causes are right and proven from the FontForge C at the release's own build.

**VERIFY.md body (ASCII, for the parent to write to /home/fsanches/compartilhado/sfd-reland/investigations/heights/VERIFY.md)**

**Model**: Claude Opus 5.5

Tools:
- babelfont f725e6a (pinned, target/release)
- babelfont ca43adc491fa (target-heights, BF only, not rebuilt)
- gftools-builder3 e851b8b (fontc 1.0.0)
- diffenator3 1.1.4
- table gate: sfd-batch5/tools/table_gate.py (sha256 008e73197f7a8736...)
- google/fonts b5efa9c32e8f; the 5 releases are byte-identical to googlefontdirectory-hg 52f780bc

Conclusions:

1. Pairing is correct. The sources are src/<X>-TTF.sfd per families.tsv, and the harness pairs by construction.

2. The pre-2012 divisor is real and dates correctly.
   - In the FontForge git history (blobless clone), 4d34d21ef866 and its twin 5817e4ae (2012-05-14) change `tot += curves[i].cnt` to `++tot`. Across the SPLMaxHeight..SFDescender block, nothing else changes between b69c9652 and 5a11aa4c except the do_max return.
   - stamp.c at b69c9652 has source_modtime 1298382513 (2011-02-22 13:48:33), which is exactly the FFTM FFTimeStamp of HerrVonMuellerhoff, Miama, NosiferCaps and UnifrakturCook. Their FFTM created/modified times equal each .sfd's CreationTime/ModificationTime.
   - The 20090914 and 20100429 builds have the same divisor. The 20120731 release has the fix.
   - Measuring the release glyf outlines independently gives the same tops and integers. The 2011 divisor gives 644 / 265 / 925,854 / 319,485.

3. PatrickHand provenance is proven:
   - release glyf == _prettfautohint.ttf glyf for all 728 glyphs
   - the .otf and the release share 727 glyphs, an identical cmap and 0 advance differences
   - FFTM sourceCreated == .otf head.created
   - the -TTF.sfd has the ttfautohint Version string and 722 TtInstrs
   - the .otf gives cap 661.449 and x 467.505; the release's own outlines and the -TTF.sfd give 660.42
   - verdict: keep OS2CapHeight 661, with the wording fixes above

4. The four 2011-rule stand-in edits are unnecessary once the fidelity flag exists; keep them only as a fallback.

5. Revise the flag proposal:
   - cutoff FFTimeStamp < 1337023489
   - state the lower bound (5fba6c9)
   - document the SplineIsLinear, RealNear and AltUni gaps

6. The us_weight_class rows are the in-progress fontc item: TTFWeight 800 and 700 are stated in the sources.

Rerun:
- `bash scratchpad/inv-heights-verify/runs.sh` (sequential)
- `gftools/venv/bin/python3 scratchpad/inv-heights-verify/indep_heights.py <release.ttf|.otf> [--blues '...'] [--em N]`
- `(cd sfd-reland && gftools/venv/bin/python3 tools/ff_heights_oracle.py families.tsv)`
- FontForge C: `git clone --bare --filter=blob:none https://github.com/fontforge/fontforge.git`, then `git show <commit>:fontforge/splinefont.c` and `git show <commit>:fontforge/stamp.c`

Everything under scratchpad/inv-heights-verify is volatile and must be copied into the repo if it is to be kept. Nothing was committed or modified outside my scratch.

## Per edit

- [keep] OS2CapHeight 661 (PatrickHand-Regular, addfield) -- The unmodified PatrickHand-Regular-TTF.sfd states no OS2CapHeight or OS2XHeight (the header has no height field and no Private BlueValues), so no designer value is discarded. The edit is minimal: only the cap row needs it, because the rule on this .sfd already yields x 467. No FontForge vintage yields 661 from these quadratic outlines (2011 rule 293, 5a11aa4c/master 660.42), so a fidelity flag cannot replace the edit. The value is not release-only: FontForge's rule on the base-tree PatrickHand-Regular.otf gives 661.449 -> 661, confirmed by my own CFF measurement. The provenance evidence also checks out: release glyf == _prettfautohint.ttf glyf for all 728 glyphs; the release adds only cvt and fpgm; the .otf shares 727 glyphs with the release, with an identical 515-entry cmap, 0 advance differences and a max bbox delta of 2.25; FFTM sourceCreated == .otf head.created; the -TTF.sfd Version carries the ttfautohint string and the file has 722 TtInstrs (_prettfautohint.sfd has 0). Verified: 0 blocking with ca43adc; with pinned f725e6a the cap row closes and nothing else changes. Two wording fixes. (1) Body: say 'exported by FontForge 20120906 from the font loaded from PatrickHand-Regular.otf', not 'exported from' the .otf. (2) value_derived_from labels the rule '5a11aa4c', but their cff probe's '2012' mode models master's SplineIsLinear (`ret &&`, absolute RealNear); 5a11aa4c has the looser form. I checked that the per-glyph tops are identical under both, so the value stands.
- [drop] OS2CapHeight 644 (HerrVonMuellerhoff-Regular, stand-in for the proposed flag) -- A fidelity explanation makes this edit unnecessary. The release FFTM FFTimeStamp is 1298382513, exactly source_modtime in stamp.c at b69c9652 (20110222). The FFTM created/modified times equal the .sfd CreationTime/ModificationTime. The b69c9652 SFStandardHeight divides by the glyph count (`tot += curves[i].cnt`), which gives 644 from this very source. The .sfd states no height. Use this only as a fallback if the converter flag is refused, and then class it as source-edit-from-source with a body naming FontForge 20110222's glyph-count mean. As a stand-in it reproduces 0 blocking.
- [drop] OS2XHeight 265 (Miama-Regular, stand-in) -- Same fidelity explanation: FFTM stamp 20110222, and the FFTM modified time equals the -TTF.sfd ModificationTime (the cubic Miama.sfd is 9 s older and carries BlueValues that the -TTF.sfd lacks). The 2011 divisor gives 7968/30 = 265. The .sfd states no height. Fallback only, as source-edit-from-source. As a stand-in: 0 blocking.
- [drop] OS2XHeight 925 + OS2CapHeight 854 (NosiferCaps-Regular, stand-ins) -- Same fidelity explanation: FFTM stamp 20110222, and the FFTM modified time (2011-10-24 13:20:44) equals the .sfd ModificationTime. No BlueValues zone bottom lies within 20.48 units. The .sfd states no height. Fallback only. As stand-ins: 1 blocking left, us_weight_class, which is the in-progress fontc item (TTFWeight: 800 is stated).
- [drop] OS2XHeight 319 + OS2CapHeight 485 (UnifrakturCook-Bold, stand-ins) -- Same fidelity explanation: FFTM stamp 20110222, and the FFTM modified time (2011-09-01 11:40:43) equals the .sfd ModificationTime. The .sfd states no height. Fallback only. As stand-ins: 1 blocking left, us_weight_class (TTFWeight: 700 is stated). The converter must measure the unrounded .sfd coordinates, as FontForge did.
- [revise] Converter flag --fontforge-height-glyph-count-mean, chosen by the release FFTM (proposed converter change) -- The mechanism is correct: 4d34d21ef866 is the only change to that code between b69c9652 and 5a11aa4c, apart from the do_max return, and ca43adc's Occurrence.count makes the one-line divisor switch straightforward. Revise four things. (1) Cutoff: FFTM stores stamp.c's source_modtime, not the commit time, so select the flag on FFTimeStamp < 1337023489 (2012-05-14T19:24:49Z, the stamp of both 4d34d21ef866 and its twin 5817e4ae), not '< 19:24:59Z'. (2) Give the lower bound: SFStandardHeight with this divisor exists from 5fba6c9 (2009-05-27). The 20090914 build (c9ca2f32) and the 20100429 build (549d3cbe) both carry `tot += curves[i].cnt` (verified), and the 20120731 release commit (63a4d0a8) has the fix, so the FFTM rule holds for every stamp in families.tsv (earliest 2009-09-14). (3) State in the help text what the flag does not model. FontForge up to at least 5a11aa4c lacks `ret &&` in SplineIsLinear and uses the relative RealNear; ca43adc ports master. For the 6 affected styles that makes no difference (their 2011 and 2012 dumps have identical per-glyph tops), but it is a gap in general. (4) ca43adc's glyphs_by_primary_codepoint ignores AltUni, while FontForge's SFFindGID/SCUniMatch matches it; this has no effect here.

## Objections

- No class is wrong. All 12 baseline blocking rows for the 5 styles are classified, and every class holds up.
- PatrickHand OS/2.sx_height [467,500] as converter-fidelity: the class stands, but the cause should say the release's 467 was computed from the .otf (467.505). The rule on this .sfd gives 467.636 and truncates to the same integer by coincidence.
- HerrVonMuellerhoff, Miama, NosiferCaps and UnifrakturCook 2011-rule rows as converter-fidelity: accepted. The evidence is exact: the FFTM FFTimeStamp equals the stamp.c at b69c9652 to the second, the FFTM created/modified times equal each .sfd, and 6 values reproduce to the integer. The class depends on the flag being built; until then the rows stay open under the pinned tools.
- PatrickHand OS/2.s_cap_height as provenance: accepted. It is not source-edit-from-release, because the value is derived from the .otf in the same base tree. I found no FontForge code path that yields 661 from the quadratic -TTF.sfd.

## Missed

- Unused corroboration: the base tree has src/Miama.otf, a FontForge 20090914 export (FFTM 2009-09-14, the c9ca2f32 stamp) with OS/2 x=132 and cap=439. Its outlines are half scale (curve sum 3984). The glyph-count mean gives 3984/30 = 132 where master gives 249. Its only flat cap top, 443, snaps to the BlueValue 439. That is a third FontForge build showing the pre-2012 divisor.
- The brief's Miama cap '898' is wrong: the oracle gives 894, the mean of the tied flats 890 and 898. They flagged only HerrVonMuellerhoff's 271.
- ff_heights_probe.py's docstring says 5a11aa4c == master for this path ('ret &&' present, RealNear absolute). That is false: 5a11aa4c has the 2011 SplineIsLinear and RealNear, and `ret &&` came later. Nothing changes here (I checked per-glyph tops identical under both for the 5 -TTF.sfd, the PatrickHand .otf and _prettfautohint.sfd), but the label is wrong.
- The FFTM cutoff is 10 s off: the stamp is 1337023489 (19:24:49Z), not the commit time 19:24:59Z. The rule's lower bound (5fba6c9, 2009-05-27) is not stated.
- UnifrakturCook-Bold-TTF.sfd has fractional coordinates that the release rounded (L, S, V tops). FontForge measured the unrounded outlines, and the converter must too. The integers are unaffected here.
- ca43adc ignores AltUni when finding list glyphs, unlike FontForge's SCUniMatch. That is a general fidelity gap with no effect on these styles.
- Nothing is committed. Their FontForge C copies and my blobless FontForge clone (scratchpad/inv-heights-verify/ff.git), indep_heights.py (sha256 a0d7179ea2e8fd36...), runs.sh (9a4b82efb1a3738a...) and runs/ are only in volatile scratch. FINDINGS.md was not written, and I did not write VERIFY.md either, because subagents are told to return findings rather than write report .md files. The parent must preserve these and write both reports.
- No rows were opened by the edits and no style was left uncovered. Nosifer-Regular and UnifrakturMaguntia-Book appear only as extra data (other units). The release-outline check confirms Nosifer's 925/854 under the 2011 divisor.
