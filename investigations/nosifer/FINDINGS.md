# nosifer -- investigation findings

**Model**: Claude Opus 5.5 (investigating agent, adversarial verifier, and the
conclusion below). Written from the agents' structured results (`results.json`).

## Conclusion

Nosifer-Regular.ttf was exported with FontForge's OpenType tables off (a legacy kern table,
no GSUB), so the source's one `liga` lookup (E E) never shipped. One documented edit drops
it. Settled 2026-09-24 by the equivalence rule (reproduce what ships, improve in later
commits): the drop stays, and restoring the ligature is listed as future work. Both height rows are FontForge 20110222's pre-2012 rule, handled by the
converter; NosiferCaps' only other row is the weight class, handled by the fontc
workaround.

## Investigator's report

# nosifer / nosifercaps -- a 2011 FontForge height rule and a non-OpenType export

**Model**: Claude Opus 5.5
**Date**: 2026-09-23. Pins: babelfont gf-sfd-conversion f725e6a (binary built 20:27, before ca43adc), gftools-builder3 e851b8b (fontc 1.0.0), diffenator3 1.1.4, table_gate.py md5 d99eadad, baseline.sh md5 e5b0b403, ff_heights_oracle.py md5 0a0921c8, fontTools 4.61.1, uharfbuzz 0.53.3, google/fonts b5efa9c32e8f. Sources: googlefontdirectory-hg 52f780bc9d19 ofl/nosifer/src/Nosifer-Regular-TTF.sfd and ofl/nosifercaps/src/NosiferCaps-Regular-TTF.sfd (the ones families.tsv names), paired with ofl/nosifer/Nosifer-Regular.ttf and ofl/nosifercaps/NosiferCaps-Regular.ttf, which are byte-identical to the monorepo copies.

## Conclusions

1. The heights 925/854 are what FontForge 20110222's own rule computes from the unmodified source. Both releases carry an FFTM table naming the FontForge build of 2011-02-22 13:48:33 (tag v20110222, 9ec8bff8). When no letter has a flat top, that build's SFStandardHeight divided the SUM OF THE DISTINCT tops by the NUMBER OF GLYPHS (splinefont.c:1709 `tot += curves[i].cnt`). The bug entered with 37d20840 (2009-05-27) and Khaled Hosny fixed it in 4d34d21e (2012-05-14, `++tot`). No Nosifer letter has a flat top:
   x-height: 18 letters, 12 distinct tops summing to 16652. The 2009-2012 rule gives 925.11 -> 925 (the release). The master rule gives 1387.67 -> 1387.
   cap height: 26 letters, 16 distinct tops summing to 22211. The 2009-2012 rule gives 854.27 -> 854 (the release). The master rule gives 1388.19 -> 1388.
   No BlueValues zone bottom (-57, 1229, 1645) lies within 20.48 of either value, so nothing snaps. The cap height falls BELOW the x-height because the cap list repeats more tops (10 repeats in 26) than the x list (6 in 18). NosiferCaps has the same glyph data, so its numbers are identical. Classification: converter-fidelity. The in-progress converter port (ca43adc) uses the master rule and would give 1387/1388, so these rows would stay blocking.

2. The Nosifer release has no GSUB because FontForge exported it with OpenType output off. The source declares liga E E -> E_E. The release has no GSUB, GPOS, GDEF or DSIG, has a legacy kern table, and has usMaxContext 1. In v20110222 tottf.c initATTables, GSUB/GPOS/GDEF and the dummy DSIG are written only in opentypemode, and the legacy kern only when neither OpenType nor Apple mode is on, which matches this table set exactly. With OpenType on, the same FontForge wrote exactly our GSUB from the identical lookup data: the NosiferCaps release of 2011-10-24 has DFLT+latn, liga [0], E E -> E_E. The Nosifer release was generated at 2011-12-19 18:44:21 UTC, the same second as Butcherman, Creepster and Eater, 10 minutes before Dave Crossland committed all four. None of the four has OpenType layout, and Butcherman's source also declares a liga its release lacks. The .sfd does not record the export mode. Classification: source-edit-from-release (verified). Effect on text: BEEF, SEE and EEE shape to E_E in our build and to E E in the release.

## Proposed .sfd edit (Nosifer-Regular only)
A new op, droplookup <lookup name>. It deletes the Lookup: line with that exact quoted name and every glyph line that fills one of its subtables. It is FATAL if the lookup is absent, has no entries, or is still referenced afterwards. Here it removes line 57 (the 'liga' Lookup line) and line 6044 in E_E (Ligature2: "'liga'" E E). E_E itself stays, because the release ships it. Subject: "Drop the E E ligature the release does not carry". Body: "Nosifer-Regular.ttf was exported with FontForge's OpenType tables off (legacy kern, no GSUB), so this liga never shipped. The absence exists only in the release; the E_E glyph stays."
DECISION for Felipe: this edit reproduces the release by removing a working ligature the designer declared. The alternative is to keep the ligature and carry the three GSUB rows as a documented improvement, as sfd-batch7/BETTER-THAN-THE-RELEASE.md proposed. In that case the build does not reproduce the release.

## Proposed converter change
An opt-in switch in the height filter (ca43adc fontforge_standard_height.rs:150) that divides by the total glyph count instead of curves.len(). baseline.sh would pass it when the release's FFTM FFTimeStamp falls in [2009-05-27, 2012-05-14). Across all 38 styles this reproduces 31 releases against 25 for the master rule alone, and breaks none (runs/heights_era_all.txt). Not build-verified, because babelfont was not rebuilt. The stand-in edit (OS2XHeight 925 / OS2CapHeight 854) closes exactly these rows. Use that stand-in as an .sfd edit only if the converter change is declined; its commit would then have to say the values are FontForge 20110222's computation.

## Runs (one build at a time)
r0 unmodified: BLOCKING 5, same as the baseline. r1 droplookup: BLOCKING 2 (heights only). r5 heights stand-in only: BLOCKING 3 (GSUB only). r2 both: CLEAN 0 with 15 stale. r3 NosiferCaps unmodified: BLOCKING 3. r4 NosiferCaps with the heights stand-in: BLOCKING 1 (us_weight_class). The shared baseline/Nosifer-Regular.gate.txt contains a table_gate.py JSONDecodeError traceback from an empty d3.json ahead of a complete gate output, which means two runs wrote to one log. r0 reproduces its 5 rows cleanly.

## Probes (investigations/nosifer/probes)
heights_2011_rule.py: do 925/854 follow from the source under the 2011 rule? heights_era_all.py: does choosing the rule by FFTM era help or hurt any style? release_provenance.py: which export, from which source state? ff_evidence.sh: prints the FontForge code at 9ec8bff8 and 4d34d21e. make_variants.py: writes the edited sources. shape_ee.py: what the missing GSUB changes in shaped text. The rerun commands are listed in verification.commands.

Rows before: Nosifer-Regular: BLOCKING 5 (GSUB.feature_list, GSUB.lookup_list, GSUB.script_list, OS/2.s_cap_height, OS/2.sx_height), 15 stale (r0, same as baseline). NosiferCaps-Regular: BLOCKING 3 (OS/2.s_cap_height, OS/2.sx_height, OS/2.us_weight_class), 16 stale (r3, same as baseline).

Rows after: Nosifer-Regular with droplookup only: BLOCKING 2, heights only (r1). With the heights stand-in only: BLOCKING 3, GSUB only (r5). With both: CLEAN 0, 15 stale (r2). NosiferCaps-Regular with the heights stand-in: BLOCKING 1, OS/2.us_weight_class, which is in progress at the converter (r4). No run opened a row, and the stale lists are unchanged.

Confidence: High. Both height rows reproduce exactly from the source under the FontForge build named in the release's FFTM, the code for that build is pinned, and the era rule gains 6 releases while breaking none. The GSUB cause rests on the release's table set matching FontForge 20110222's non-OpenType code path, the NosiferCaps release's GSUB matching ours, and the 2011-12-19 batch timestamps. The droplookup edit is gate-verified (r1, r2 CLEAN 0). The converter change is verified only through a stand-in edit, not a babelfont build.

## Rows

| style | row | class | cause |
|---|---|---|---|
| Nosifer-Regular | OS/2.sx_height [925, 500] | converter-fidelity | FontForge 20110222 (the FontForge build named in the release's FFTM: FFTimeStamp 2011-02-22 13:48:33, tag v20110222 = 9ec8bff8) ran SFStandardHeight with a bug in the no-flat-tops branch: it divided the SUM OF THE DISTINCT tops by the NUMBER OF GLYPHS (splinefont.c:1709 `tot += curves[i].cnt`). No Nosifer letter has a flat top, so the result is 16652/18 = 925.11 -> 925. The bug entered with 37d20840 (2009-05-27) and Khaled Hosny fixed it in 4d34d21e (2012-05-14, `++tot`). The master rule, which the oracle and the in-progress ca43adc port both use, gives 16652/12 = 1387.67 -> 1387. |
| Nosifer-Regular | OS/2.s_cap_height [854, 700] | converter-fidelity | Same FontForge 20110222 rule: 26 capitals (A-Z) share 16 distinct tops, giving 22211/26 = 854.27 -> 854. The master rule gives 22211/16 = 1388.19 -> 1388. The cap height falls BELOW the x-height because the cap list repeats more tops (10 repeats in 26) than the x list (6 in 18). The lowercase tops equal the capitals' letter for letter. |
| Nosifer-Regular | GSUB.script_list [null, {DFLT/dflt, latn/dflt: [0]}] | source-edit-from-release | The release was exported on 2011-12-19 with FontForge's OpenType output turned off. v20110222 tottf.c initATTables writes GSUB, GPOS, GDEF and the dummy DSIG only in opentypemode, and writes the legacy kern table only when neither OpenType nor Apple mode is on. The release matches that exactly: kern present, no GSUB/GPOS/GDEF/DSIG, usMaxContext 1. The source declares liga E E -> E_E, and the .sfd does not record the export mode, so the missing GSUB exists only in the release. |
| Nosifer-Regular | GSUB.feature_list [null, {liga: [0]}] | source-edit-from-release | Same as script_list: the release was exported with FontForge's OpenType tables off, so the declared liga feature was never written. |
| Nosifer-Regular | GSUB.lookup_list [null, {0: ligature E E -> E_E}] | source-edit-from-release | Same as script_list. The release still ships the E_E glyph, but it is unreachable. |
| NosiferCaps-Regular | OS/2.sx_height [925, 500] | converter-fidelity | Identical glyph data and the same FontForge 20110222 build (FFTM), so the same 2009-2012 rule applies: 16652/18 -> 925. The master rule gives 1387. |
| NosiferCaps-Regular | OS/2.s_cap_height [854, 700] | converter-fidelity | Same 2009-2012 rule: 22211/26 -> 854. The master rule gives 1388. |
| NosiferCaps-Regular | OS/2.us_weight_class [800, 400] | converter-fidelity | The .sfd states TTFWeight: 800. fontc does not set usWeightClass for a static single-master source. Someone else is fixing this at the converter. |

## Proposed .sfd edits

- **Drop the E E ligature the release does not carry** (Nosifer-Regular) `droplookup 'liga' Standard Ligatures in Latin lookup 0` -- verified: True; value from: The release has no GSUB table. The export mode was identified from FontForge v20110222 tottf.c initATTables (layout tables only in opentypemode; legacy kern only when neither OpenType nor Apple mode is on) and the release's table set (kern only, usMaxContext 1).; the source stated: Line 57: Lookup: 4 0 1 "'liga' Standard Ligatures in Latin lookup 0"  {"'liga'"  } ['liga' ('DFLT' <'dflt' > 'latn' <'dflt' > ) ]. In glyph E_E, line 6044: Ligature2: "'liga'" E E. The edit removes exactly these 2 lines.

## Proposed converter changes

- Height rule for FontForge builds from 2009-05-27 to 2012-05-14. Add an opt-in fidelity switch to the in-progress height filter (ca43adc babelfont/src/filters/fontforge_standard_height.rs:150). When no letter has a flat top, it should divide the sum of the distinct round/pointed tops by the total glyph count (sum of the per-height counts) instead of the number of distinct tops. That was FontForge's SFStandardHeight from 37d20840 (2009-05-27) until 4d34d21e (2012-05-14, Khaled Hosny's fix). The flat-top branch and the BlueValues snap stay unchanged: v20110222 and 2012-06-28 splinefont.c differ only in this line and in the do_max=false no-glyph return, which descender-only code uses. baseline.sh can choose the switch from the release like its other decisions: pass it when the release's FFTM FFTimeStamp falls in [2009-05-27, 2012-05-14), and use the master rule otherwise or when FFTM is missing. Without this, ca43adc gives Nosifer 1387/1388 and the rows stay blocking.

  Evidence: runs/heights_2011_rule.txt reproduces Nosifer and NosiferCaps at 925/854 exactly (16652/18 and 22211/26). runs/heights_era_all.txt covers all 38 families.tsv styles: choosing the rule by era reproduces 31 releases, against 25 for the master rule alone, and breaks none. The added styles are Nosifer, NosiferCaps, HerrVonMuellerhoff (269/644), Miama (265/894), UnifrakturCook-Bold (319/485) and UnifrakturMaguntia-Book (1095/1409). The last four were run through the probe only, not the gate. runs/ff_evidence.txt and runs/ff_splinefont_history.txt pin the code and the commits. This is not build-verified, because babelfont was not rebuilt. As a stand-in, stating OS2XHeight 925 and OS2CapHeight 854 in a copy of the source closes exactly these rows (r2 CLEAN 0, r4 only us_weight_class left, r5 only GSUB left).

## Unresolved

- FINDINGS.md was NOT written: the harness refused a Write of a .md report file ('Subagents should return findings as text'). Its full intended text is in verification.summary, ready for the orchestrator to write to /home/fsanches/compartilhado/gf-source-modernization/investigations/nosifer/FINDINGS.md. The probes, runs and edits under investigations/nosifer/ were written.
- Decision for Felipe on the GSUB rows. The droplookup edit reproduces the release but removes a working liga the designer declared; BEEF, SEE and EEE shape differently. The alternative is to keep the liga and document the 3 rows as an improvement, in which case the build does not reproduce the release. Butcherman (not in families.tsv) lost a declared liga in the same 2011-12-19 export batch.
- The height converter change is not build-verified: babelfont may not be rebuilt in this unit. It is verified only through the stand-in edit that states the target values (r2, r4, r5). It also bears on the other converter work (ca43adc), which implements only the master rule.
- The shared baseline file gf-source-modernization/baseline/Nosifer-Regular.gate.txt contains a table_gate.py JSONDecodeError traceback (empty d3.json) ahead of a complete gate output, a sign of two concurrent runs writing one log. The row set stands (r0 reproduces it cleanly), but the file was left untouched.
- Outside this unit: the era-chosen height rule leaves 7 of 38 styles unexplained. They are PatrickHand-Regular (FontForge 2012-09-06, cap 660 against 661), Puritan x4 (495/640 against 507/655) and Tuffy x2 (no FFTM; release 500/700).

## Rerun

    cd /home/fsanches/compartilhado/gf-source-modernization; I=investigations/nosifer; PY=/home/fsanches/compartilhado/gftools/venv/bin/python3
    $PY $I/probes/heights_2011_rule.py > $I/runs/heights_2011_rule.txt
    $PY -W ignore $I/probes/heights_era_all.py > $I/runs/heights_era_all.txt
    $PY $I/probes/release_provenance.py > $I/runs/release_provenance.txt
    sh $I/probes/ff_evidence.sh <scratch-dir> > $I/runs/ff_evidence.txt
    git clone --filter=blob:none --no-checkout https://github.com/fontforge/fontforge.git ff-git && git -C ff-git log --format='%h %ad %an | %s' --date=short 37d20840^..e4aa2e030c7db9fbd9f52010a96170508acdb49e -- fontforge/splinefont.c
    $PY $I/probes/make_variants.py $I/edits
    TAG=nosifer OUT=$PWD/$I/runs/r0-unmodified bash tools/baseline.sh Nosifer-Regular
    TAG=nosifer OUT=$PWD/$I/runs/r1-droplookup SRC_OVERRIDE=$PWD/$I/edits/Nosifer-Regular.droplookup.sfd bash tools/baseline.sh Nosifer-Regular
    TAG=nosifer OUT=$PWD/$I/runs/r5-heights-only SRC_OVERRIDE=$PWD/$I/edits/Nosifer-Regular.heights.sfd bash tools/baseline.sh Nosifer-Regular
    TAG=nosifer OUT=$PWD/$I/runs/r2-droplookup+heights SRC_OVERRIDE=$PWD/$I/edits/Nosifer-Regular.droplookup+heights.sfd bash tools/baseline.sh Nosifer-Regular
    TAG=nosifer OUT=$PWD/$I/runs/r3-caps-unmodified bash tools/baseline.sh NosiferCaps-Regular
    TAG=nosifer OUT=$PWD/$I/runs/r4-caps-heights SRC_OVERRIDE=$PWD/$I/edits/NosiferCaps-Regular.heights.sfd bash tools/baseline.sh NosiferCaps-Regular
    $PY $I/probes/shape_ee.py /home/fsanches/compartilhado/google/fonts/ofl/nosifer/Nosifer-Regular.ttf <scratchpad>/baseline/Nosifer-Regular-nosifer/fonts/ttf/Nosifer-Regular.ttf
