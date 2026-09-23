# heights -- investigation findings

**Model**: Claude Opus 5.5 (investigating agent, adversarial verifier, and the
conclusion below). Written from the agents' structured results (`results.json`).

## Conclusion

The height rows the current FontForge rule does not reproduce are, with one exception,
FontForge's own older rule. Until commit 4d34d21ef866 (2012-05-14) `SFStandardHeight`
divided the sum of the distinct round tops by the number of GLYPHS. HerrVonMuellerhoff,
Miama, NosiferCaps and UnifrakturCook were exported by FontForge 20110222 (the FFTM stamp),
which gives exactly their released values: UnifrakturCook's 319/485 where today's rule
gives 1087/1577. babelfont gf-sfd-conversion 8b59bc3 adds
`--fontforge-height-glyph-count-mean`; tools/recipe.py passes it when the release's FFTM
stamp is below 1337023489. Selecting the rule by vintage reproduces 29 of 38 styles, against
23 with today's rule alone, and no pre-2012 style matches only under today's rule
(`vintage_selection.txt`, `probe_all.txt`). The old divisor entered in FontForge 37d20840
(2009-05-27); the report below cites 5fba6c9, the same change in a history with no common
ancestor with 4d34d21ef866 (GitHub compare API: 37d20840 is 740 commits behind the fix).

The exception is PatrickHand: its release was exported from the cubic
`src/PatrickHand-Regular.otf` (cap height 661), while the `.sfd` re-imports the hinted
release (660). One documented edit, `OS2CapHeight 661`.

## Investigator's report

Pinned tools: babelfont gf-sfd-conversion f725e6a (target/release, the pinned build) and
ca43adc (target-heights/release, BUILT_FROM=ca43adc, used as BF only, not rebuilt);
gftools-builder3 e851b8b (fontc 1.0.0); diffenator3; sfd-batch5/tools/table_gate.py;
releases google/fonts b5efa9c32e8f, byte-identical to the .ttf files in
googlefontdirectory-hg 52f780bc. The oracle port is correct. An independent re-
implementation from the C (ff_heights_probe.py) agrees with it on all 38 styles. It also
finds four minor divergences, none of which changes a value: AltUni is ignored, file
order is used instead of the lowest gid, MinMaxWithin's t2=-1 root is skipped, and only
master's tolerances are modelled. Root causes: four styles need FontForge's
pre-2012-05-14 glyph-count curve mean (a converter fidelity flag, selected by the
release's FFTM build date), verified through stand-in .sfd statements. For PatrickHand
the provenance is established: the cap height was computed from the cubic .otf outlines,
and the edit OS2CapHeight 661 was verified. The remaining x/cap rows close with the
ca43adc rule already in progress; the us_weight_class rows are the in-progress fontc
item.

Rows before: Pinned babelfont f725e6a (same as the baseline/): HerrVonMuellerhoff sx [269,500] cap [644,700]; Miama sx [265,500] cap [894,700]; NosiferCaps wc [800,400] sx [925,500] cap [854,700]; PatrickHand sx [467,500] cap [661,700]; UnifrakturCook wc [700,400] sx [319,500] cap [485,700]. With the ca43adc height rule (BF=target-heights build): HerrVonMuellerhoff cap [644,761] (1 blocking); Miama sx [265,498] (1); NosiferCaps wc, sx [925,1387], cap [854,1388] (3); PatrickHand cap [661,660] (1); UnifrakturCook wc, sx [319,1087], cap [485,1577] (3).

Rows after: ca43adc plus the tested source copies (edits/). HerrVonMuellerhoff (OS2CapHeight 644): 0 blocking, 6 stale. Miama (OS2XHeight 265): 0 blocking, 1 stale. NosiferCaps (OS2XHeight 925, OS2CapHeight 854): 1 blocking, us_weight_class [800,400], 16 stale. PatrickHand (OS2CapHeight 661, the proposed edit): 0 blocking, 45 stale. UnifrakturCook (OS2XHeight 319, OS2CapHeight 485): 1 blocking, us_weight_class [700,400], 22 stale. Every gate printed its closing 'N blocking table difference(s)' line. Apart from the height rows, each gate is identical line for line to its before-ca43adc gate, stale rows included.

Confidence: High. Two independent implementations of the rule agree with each other, and with the babelfont ca43adc port, on every style. The pre-2012 divisor is read directly in the FontForge C at the release's own FFTM build date. For PatrickHand, the cubic-.otf computation matches the release exactly (661.449 gives 661), and four independent file facts tie the release to that .otf. Every proposed value closed its row in the harness without changing any other gate line.

## Rows

| style | row | class | cause |
|---|---|---|---|
| HerrVonMuellerhoff-Regular | OS/2.sx_height [269, 500] | converter-fidelity | Converter work in progress (ca43adc). FontForge's master rule already gives 269 from this source because the tops are flat (flat mode 269). The pinned f725e6a converter writes the default 500. Note: the brief says the rule gives 271, but it gives 269. |
| HerrVonMuellerhoff-Regular | OS/2.s_cap_height [644, 700] | converter-fidelity | The release was exported by FontForge 20110222 (FFTM build 2011-02-22 13:48:33). From 5fba6c9 (2009-05-27) until 4d34d21ef866 (2012-05-14), SFStandardHeight divided the sum of the DISTINCT curve heights by the number of GLYPHS (`tot += curves[i].cnt`). No A-Z top here is flat: 16758/26 = 644.54, so 644. Master divides by 22 distinct heights: 761. |
| Miama-Regular | OS/2.sx_height [265, 500] | converter-fidelity | FontForge 20110222's glyph-count curve mean: 7968/30 = 265.6, so 265. Master gives 7968/16 = 498. No flat tops, and no BlueValues in this .sfd. |
| Miama-Regular | OS/2.s_cap_height [894, 700] | converter-fidelity | Converter work in progress (ca43adc). Flat mode 894 under both FontForge vintages. The cubic Miama.sfd in the tree gives 886, so the -TTF.sfd is the state that was measured. |
| NosiferCaps-Regular | OS/2.sx_height [925, 500] | converter-fidelity | FontForge 20110222's glyph-count curve mean: 16652/18 = 925.11, so 925. Master gives 16652/12 = 1387. No BlueValues zone bottom falls within 20.48 units. |
| NosiferCaps-Regular | OS/2.s_cap_height [854, 700] | converter-fidelity | FontForge 20110222's glyph-count curve mean: 22211/26 = 854.27, so 854. Master gives 22211/16 = 1388. |
| NosiferCaps-Regular | OS/2.us_weight_class [800, 400] | converter-fidelity | Converter work in progress (fontc 1.0.0 ignores a static single-master weightClass). The .sfd states TTFWeight: 800. |
| PatrickHand-Regular | OS/2.sx_height [467, 500] | converter-fidelity | Converter work in progress (ca43adc). The master rule on this source gives 467.64, so 467. The release's own export gives 467.505, so 467, which is the same value. |
| PatrickHand-Regular | OS/2.s_cap_height [661, 700] | provenance | The release was not exported from this .sfd. It is src/PatrickHand-Regular_prettfautohint.ttf plus ttfautohint. That TTF is an export by FontForge build 2012-09-06 (which already has `++tot`) of the font loaded from src/PatrickHand-Regular.otf. FontForge measured the .otf's cubic outlines: 15 distinct round tops, mean 661.449, so 661. The -TTF.sfd is a later re-import of the hinted release. Its quadratic tops differ for B (667.97->668), F (658.54->658), Y (665.26->666), Z (662.96->664) and T (round->pointy), giving 12 distinct tops and 7925/12 = 660.42, so 660. |
| UnifrakturCook-Bold | OS/2.sx_height [319, 500] | converter-fidelity | FontForge 20110222's glyph-count curve mean: 5436/17 = 319.76, so 319. Master gives 5436/5 = 1087. |
| UnifrakturCook-Bold | OS/2.s_cap_height [485, 700] | converter-fidelity | FontForge 20110222's glyph-count curve mean: 12617.264/26 = 485.28, so 485. Master gives 12617.264/8 = 1577. |
| UnifrakturCook-Bold | OS/2.us_weight_class [700, 400] | converter-fidelity | Converter work in progress (fontc static weight class). The .sfd states TTFWeight: 700. |

## Proposed .sfd edits

- **OS2CapHeight 661** (PatrickHand-Regular) `addfield OS2CapHeight 661` -- verified: True; value from: FontForge's SFStandardHeight at 5a11aa4c (2012-09-06, the release's FFTM build) applied to the cubic CFF outlines of src/PatrickHand-Regular.otf in the same base tree: mean of 15 distinct round tops = 661.4486, so 661. That equals the release's sCapHeight. The value is derived from a file in the base tree; it does not exist only in the release.; the source stated: No OS2CapHeight or OS2XHeight line. Header: Ascent 800, Descent 200, order-2 layers, no BlueValues. The exporter rule on this .sfd's own quadratic outlines gives 660.

## Proposed converter changes

- Proposed change in babelfont filters/fontforge_standard_height.rs, fn standard_height, curve branch. Add an opt-in fidelity flag, for example --fontforge-height-glyph-count-mean. Help text: 'Reproduce a TTF exported by a FontForge built before 2012-05-14 (fontforge 4d34d21ef866): SFStandardHeight divided the sum of the distinct round/pointed top heights by the number of glyphs, not by the number of distinct heights.' With the flag, the divisor is curves.iter().map(|o| o.count).sum() instead of curves.len(). Recipe change (baseline.sh / recipe.py), decided from the release like the other fidelity decisions: pass the flag when the release has an FFTM table whose FFTimeStamp is before 2012-05-14T19:24:59Z. With no FFTM, or a later build, keep the master rule. Fallback if the flag is rejected: state the same values as .sfd edits (the tested stand-ins in edits/*-2011rule.sfd); these would be classed source-edit-from-source.

  Evidence: 1. FontForge C: the glyph-count divisor (`tot += curves[i].cnt`) is in splinefont.c at 5fba6c9 (2009-05-27), b69c9652 (2011-02-22) and f316d0f6 (the parent of 4d34d21ef866). 4d34d21ef866 (2012-05-14T19:24:59Z, 'it was dividing by the wrong value') changes it to `++tot`, which 5a11aa4c (2012-09-06) and master keep. Nothing else in SPLMaxHeight..SFXHeight differs between b69c9652 and 5a11aa4c. 2. Selecting the rule by the release's FFTM build reproduces 29 of the 36 styles that do not state heights, against 23 with the master rule alone (31 of 38 counting ComicRelief's stated values, against the oracle's 25). It breaks no style that master reproduces (vintage_selection.txt). The 2011 rule applied everywhere would break PatrickHand x (257), so selection is required. 3. Stand-ins: stating the 2011-rule values in copies of the four sources and converting with babelfont ca43adc closes every height row. Before those edits the ca43adc harness showed 1/1/3/3 blocking; after, 0/0/1/1, and the remaining rows are us_weight_class only. The gates are otherwise identical line for line (nothing_else_opened.sh).

## Unresolved

- FINDINGS.md was NOT written. The Write tool refused it ('Subagents should return findings as text, not write report files'), and I did not bypass that through the shell. Its content is in this result. The evidence it would cite is under /home/fsanches/compartilhado/sfd-reland/investigations/heights/: ff_heights_probe.py (sha256 70e11942...), cff_heights_probe.py (6f06eb7a...), rerun.sh, summarize.sh, nothing_else_opened.sh, probe_all.txt, vintage_selection.txt, dump-*.txt, cff-PatrickHand-Regular.otf-2012.txt, edits/*.sfd and runs/{before-f725e6a,before-ca43adc,after-ca43adc}/. The parent should write FINDINGS.md from this result, or have the rule relaxed.
- The converter flag (--fontforge-height-glyph-count-mean) is only proposed. Per the rules I did not build babelfont, so the four converter-fidelity rows were verified through stand-ins: the 2011-rule values stated in source copies. The flag itself still needs a build and a harness rerun. The recipe needs a new release-derived decision: FFTM FFTimeStamp < 2012-05-14T19:24:59Z.
- The after runs used the ca43adc build (target-heights) because the pinned f725e6a has no height rule. With f725e6a, PatrickHand's x row [467,500] stays open until ca43adc is pinned.
- FontForge 'real' is assumed to be double (FONTFORGE_CONFIG_USE_DOUBLE). The configuration of the 2011/2012 distro builds is not documented. On these integer-coordinate order-2 sources the float variant does not change any top.
- The FontForge C read for this unit (b69c9652, 5a11aa4c, f316d0f6, 4d34d21e, 5fba6c9 copies of splinefont.c, tottf.c, sfd.c, splineutil*.c, splineorder2.c, fvfonts.c) is only in volatile scratch: .../scratchpad/inv-heights/ff/. It can be refetched from https://raw.githubusercontent.com/fontforge/fontforge/<commit>/fontforge/<file>. Per the task rules nothing was committed.
- The brief quoted HerrVonMuellerhoff's rule value as 271/761. The oracle, the probe and the ca43adc port all give 269/761, and 269 is the release's x-height.

## Rerun

    cd /home/fsanches/compartilhado/sfd-reland/investigations/heights && bash rerun.sh probes   # probe_all.txt, dump-*-{2011,2012}.txt, cff-PatrickHand-Regular.otf-2012.txt, vintage_selection.txt
    bash rerun.sh builds   # sequential. For each style: before-f725e6a (pinned), BF=<ca43adc> before-ca43adc, BF=<ca43adc> SRC_OVERRIDE=edits/<x>.sfd after-ca43adc. Harness: tools/baseline.sh with TAG=heights OUT=runs/<name>
    sh summarize.sh; bash nothing_else_opened.sh
    /home/fsanches/compartilhado/gftools/venv/bin/python3 /home/fsanches/compartilhado/sfd-reland/tools/ff_heights_oracle.py   # cross-check: 25/38, same values as ff_heights_probe.py master column
