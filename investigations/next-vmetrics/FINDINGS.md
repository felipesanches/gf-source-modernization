# next-vmetrics -- investigation findings

**Model**: Claude Opus 5.5 (investigating agent, adversarial verifier, and the
conclusion below). Written from the agents' structured results (`results.json`).

## Conclusion

Limelight needs one documented edit reproducing the 2012 Google Fonts vertical-metrics
change. Mountains of Christmas Bold and Nothing You Could Do need a new babelfont filter
(--fontforge-legacy-offset-metrics: FontForge before 2014-09-16 resolved offset metrics
against the on-curve bbox), chosen by the release's FFTM stamp.

## Investigator's report

All 11 blocking rows of the three styles close. Limelight 5 -> 0 with the documented
.sfd edit on the pinned converter (runs/01), and also with the prototype filter present
(runs/04). MountainsofChristmas-Bold 4 -> 1 with the prototype babelfont filter
(runs/02) -> 0 with land.py's existing weight-class workaround (runs/03).
NothingYouCouldDo 2 -> 0 with the filter (runs/02). MountainsofChristmas-Regular stays
CLEAN (runs/02). The same filter takes the precedent UnifrakturMaguntia-Book from 5 to 3
rows (runs/05 -> 06), leaving only the GPOS shell, which is another unit's. The
regression sweep over 149 styles shows the filter changes only 4 styles and moves no
metric away from its release.

Rows before: 11 (runs/00-baseline, which reproduces baseline-next): Limelight-Regular 5 (s_typo_ascender, us_win_ascent, us_win_descent, hhea.ascender, hhea.descender), MountainsofChristmas-Bold 4 (us_win_ascent, us_win_descent, hhea.descender, us_weight_class), NothingYouCouldDo 2 (us_win_ascent, hhea.ascender)

Rows after: 0: Limelight-Regular 0 (runs/01 and runs/04), MountainsofChristmas-Bold 0 (runs/03; 1 in runs/02 before land.py's weight-class workaround), NothingYouCouldDo 0 (runs/02)

Confidence: High for every row's cause. The MountainsofChristmas-Bold and NothingYouCouldDo values are reproduced exactly from the unmodified sources using FontForge's code at the commit whose stamp.c equals the releases' FFTM build (b69c9652, 1298382513). A buildable prototype closes them in the harness with no regression across 149 styles. High that Limelight's metrics are a post-export release edit: head.created != head.modified, glyph boxes were recomputed over all points, and five values equal vmetcheck.py's rule, not FontForge's export of the source. Medium on which tool made that edit. The prototype's exact shape (filter vs reader option, name) is still to be settled upstream.

## Rows

| style | row | class | cause |
|---|---|---|---|
| Limelight-Regular | OS/2.s_typo_ascender [1864, 1881] | source-edit-from-release | The release was edited after FontForge exported it. FontForge 20090914 exports this .sfd's offset-mode OS2TypoAscent 243 as Ascent 1638 + 243 = 1881, which is also what our build gives. The shipped 1864 is int() of the source's true outline maximum (1864.0, uni1E1F). That is the rule googlefontdirectory's tools/bbox/vmetcheck.py (hg 927784141) prescribed for win, typo and hhea. |
| Limelight-Regular | OS/2.us_win_ascent [1864, 1881] | source-edit-from-release | Same post-export edit. FontForge's WinBB gives head.yMax 1864 + stated offset 17 = 1881 (our build agrees). The release carries 1864 = int(true max 1864.0), vmetcheck.py's value. |
| Limelight-Regular | OS/2.us_win_descent [629, 633] | source-edit-from-release | Same post-export edit. FontForge 20090914 exports -floor(on-curve min -628, kcommaaccent) + 3 = 631. babelfont 496e904 exports -floor(true min -629.28) + 3 = 633. The release has 629 = -int(-629.28), vmetcheck.py's value. No converter rule gives 629 from the stated offset 3. |
| Limelight-Regular | hhea.ascender [1864, 1881] | source-edit-from-release | Same post-export edit. FontForge's sethhead gives max(int(1864.0), head.yMax 1864) + 17 = 1881. The release has 1864, vmetcheck.py's value. |
| Limelight-Regular | hhea.descender [-629, -633] | source-edit-from-release | Same post-export edit. FontForge 20090914 gives min(int(-629.28) = -629, head.yMin -628) - 3 = -632, and babelfont 496e904 gives floor(-629.28) - 3 = -633. The release has -629 = int(-629.28), vmetcheck.py's value. The edit left only the typo descender (-634 = -Descent 410 - 224) at FontForge's value, although vmetcheck would have changed it too. |
| MountainsofChristmas-Bold | OS/2.us_win_ascent [1064, 1066] | converter-fidelity | This is FontForge 20110222's head box. SplineSetQuickBounds before ee15007274e9 (2014-09-16) counts ON-CURVE points only. Scaron's highest on-curve point ceils to 1056, while its control point reaches 1060 and the curve 1058.0. So win = 1056 + stated offset 8 = 1064. babelfont 496e904 (#85) uses ceil(true max 1058.0) + 8 = 1066. |
| MountainsofChristmas-Bold | OS/2.us_win_descent [354, 355] | converter-fidelity | Same rule. g's lowest on-curve point floors to -354 (true curve -354.381, control point -356), so win descent = 354 + 0. #85's floor(true min) gives 355. |
| MountainsofChristmas-Bold | hhea.descender [-354, -355] | converter-fidelity | FontForge's sethhead: the int of the TRUE bounds (C truncation toward zero: -354.381 -> -354), widened to the head box (-354), plus the stated 0 gives -354. #85 uses floor(-354.381) = -355. hhea.ascender already matches (max(int 1058, 1056) + 8 = 1066). |
| MountainsofChristmas-Bold | OS/2.us_weight_class [700, 400] | compiler-gap | fontc 1.0.0 ignores a single-master Glyphs source's instance weightClass (issues/fontc-static-weight-class.md). tools/land.py already closes this with tools/workarounds.py weight_class, which takes TTFWeight 700 from the .sfd and writes it as FEA. baseline.sh does not apply land.py's workarounds, so it reports the row. This is not a vmetrics row. |
| NothingYouCouldDo | OS/2.us_win_ascent [959, 960] | converter-fidelity | FontForge 20110222's on-curve head box: Ecircumflex's highest on-curve point ceils to 959, while the curve reaches 959.439 and a control point 962. So win = 959 + 0. #85's ceil(true max) gives 960. |
| NothingYouCouldDo | hhea.ascender [959, 960] | converter-fidelity | sethhead: max(int(959.439) = 959, head.yMax 959) + 0 = 959. #85 gives ceil(959.439) = 960. |

## Proposed .sfd edits

- **Set the vertical metrics the 2012 release carries** (Limelight-Regular) `setfield OS2TypoAscent 1864; OS2TypoAOffset 0; OS2WinAscent 1864; OS2WinAOffset 0; OS2WinDescent 629; OS2WinDOffset 0; HheadAscent 1864; HheadAOffset 0; HheadDescent -629; HheadDOffset 0` -- verified: True; value from: Copied from the release, and disclosed as such: google/fonts b5efa9c32e8f ofl/limelight/Limelight-Regular.ttf, blob 879e7f9d, identical to googlefontdirectory-hg 927784141. These values are a post-export edit. They equal int() of this source's true outline extremes (max 1864.0 on uni1E1F, min -629.28 on kcommaaccent), the rule of googlefontdirectory-hg 927784141:tools/bbox/vmetcheck.py. So they can be derived from the source outlines as well as read from the release. The typo descender the edit left alone (-634) is not touched here.; the source stated: OS2TypoAscent: 243 / OS2TypoAOffset: 1, OS2WinAscent: 17 / OS2WinAOffset: 1, OS2WinDescent: 3 / OS2WinDOffset: 1, HheadAscent: 17 / HheadAOffset: 1, HheadDescent: -3 / HheadDOffset: 1. These are offsets, which FontForge 20090914 exports as 1881 / 1881 / 631 / 1881 / -632, the designer's intent: the designer's own src/Limelight-Regular.otf carries 1881/-634 in typo, win and hhea.

## Proposed tool changes

- **babelfont-rs (simoncozens/babelfont-rs)**: A new opt-in filter, --fontforge-legacy-offset-metrics, in the 'reproducing a legacy FontForge export' group. It re-resolves a FontForge source's offset-mode usWinAscent, usWinDescent and hhea ascender/descender against the bases FontForge's exporter used before ee15007274e9 (2014-09-16). Win: floor/ceil of each glyph's ON-CURVE points over decomposed default-master layers; the SFD reader keeps every SplinePoint, including interpolated quadratic ones, as an on-curve node. hhea: the true outline extremes truncated toward zero, widened to that box, and to 0 when a glyph is empty. The reader also records each metric's stated delta (format_specific 'sfd.offset_delta.<key>') so the filter does not depend on the reader's own base rule. After resolving, the filter marks the metric absolute (offset flag '0', offset_mode marker removed), so an SFD write-back stays consistent. The #85 default (floor/ceil of the true outline) is unchanged. The prototype adds 319 lines: 9 in fontforge.rs, 1 in filters/mod.rs, and the new filters/fontforgelegacyoffsetmetrics.rs with 3 unit tests.

  Evidence: Harness, rows before -> after: MountainsofChristmas-Bold 4 -> 1 (runs/02; the remaining row is us_weight_class) -> 0 with land.py's workarounds (runs/03). NothingYouCouldDo 2 -> 0 (runs/02). MountainsofChristmas-Regular stays 0 (runs/02). UnifrakturMaguntia-Book, the precedent, 5 -> 3, with only the GPOS shell left (runs/05 -> runs/06). Conversion sweep over all 149 styles of families.tsv + families-next.tsv (runs/proto_metrics_sweep.txt): six metrics per style match the release 851 times with the filter vs 844 without, and the filter changes exactly 4 styles (UnifrakturMaguntia-Book, MountainsofChristmas-Bold, NothingYouCouldDo, Limelight-Regular). No value moves away from its release. The model sweep (runs/offset_bases_sweep.txt, 328 offset-mode metrics in 82 styles, all quadratic): pre-2014 rule 305, #85 298, FontForge-master rule 295. The pre-2014 rule never misses a metric #85 gets. Its 23 misses are Limelight (release edit), Play-Bold (no FFTM) and Puritan (em scale, its own plan). The PR #85 evidence pairs (hg -TTF .sfd vs GF release, runs/offset_bases_pr85_evidence.txt): the pre-2014 rule gets copse, daysone and handlee 12/12, #85 8/12. copse ships 1991, not the 1992 #85's message claims; sfd-batch5/tools/probes/sfd_bbox_rounding/README.md recorded that before #85 merged. FontForge source at the FFTM builds: runs/ff-excerpts.txt. Checks (runs/babelfont-proto-checks.txt): fmt clean; clippy --all-targets -D warnings clean; lib tests 259 pass, and the 11 failures are the robocjk/decompose tests that need the absent noto-cjk-varco data, which fail identically on upstream 496e904.
  Upstream: Yes, a new PR to simoncozens/babelfont-rs. Felipe must open it (no GitHub write access). The filter registration goes in the 'Filters for reproducing a legacy FontForge export' group that our open PRs #91-#93 introduce, so it rebases after them, or it carries its own group line on plain 496e904. Until it merges, land.py refuses to cite the converter, so MountainsofChristmas and NothingYouCouldDo land only as *-UNPUBLISHED-CONVERTER.
- **gf-source-modernization tools/recipe.py**: Pass --fontforge-legacy-offset-metrics FIRST (it measures the outlines as the source states them, before --snap-component-transforms moves any component) when the release's FFTM FontForge build stamp is before 1410896146 (2014-09-16T19:35:46Z, ee15007274e9). This uses the same FFTM mechanism as --fontforge-height-glyph-count-mean. Releases without FFTM do not get the flag.

  Evidence: Every FFTM stamp in both tables is 2012-09-06 or earlier. With the flag on every style, only the 4 styles above change and none regresses (runs/proto_metrics_sweep.txt), so gating by stamp is safe for these tables.
  Upstream: No, it is a workspace tool. Apply it once the babelfont PR is merged and the pinned converter is rebuilt from a published revision.

## Families that land once these are in

- limelight (the .sfd edit alone on the current converter, 496e904 + #91-#93: runs/01 CLEAN; like every landing it waits on #91-#93 being merged upstream)
- nothingyoucoulddo (babelfont filter + recipe change: runs/02 CLEAN)
- mountainsofchristmas (Bold: babelfont filter + recipe change + land.py's existing weight-class workaround, runs/03 CLEAN; Regular already CLEAN and still CLEAN with the filter, runs/02)

## Decisions for Felipe

- Limelight: approve reproducing the 2012 Google Fonts vertical-metrics edit as one documented .sfd commit. Its five values are copied from the release, and the commit says so; they equal googlefontdirectory's own vmetcheck.py rule applied to the source outlines. The alternative is to keep the designer's offsets (1881/-634), leaving 5 blocking rows and breaking the equivalence rule. Suggested future_work entry for the plan: 'Restore the vertical metrics the source states (typo/win/hhea ascent 1881, descent 631-634, as the designer's own OTF carries): revert the 2012 metrics commit.'
- Open the babelfont-rs PR for --fontforge-legacy-offset-metrics. The name and shape are your call and Simon's; he may prefer a reader option to a filter. It needs your push and PR (no GitHub write access here).
- Whether to tell Simon that #85's default (floor/ceil of the TRUE outline) matches no FontForge vintage when a control point lies beyond a curve's extreme. Pre-2014 FontForge used on-curve points; FontForge after ee15007274e9 uses all points. Also, #85's commit message evidence (copse 1992, daysone 568) is contradicted by the hg-source vs GF-release pairs (1991, 567). No post-2014 release in either table can validate a different default.
- Apply the recipe.py diff (FFTM stamp < 2014-09-16 -> flag first) once the converter PR is merged.

## Unresolved

- GiveYouGlory (sfd-batch5, not in families.tsv or families-next.tsv) is the one known pair where the pre-2014 rule loses to #85: hhea.descender -624 vs release -625 (#85 gets -625). Its win descent 621 matches no rule (619 / 627 / 622). 621 = -int(-621.86) is vmetcheck's value, which suggests another post-export edit, but it was not investigated. If it is ever re-landed with this recipe, check it first (runs/offset_bases_pr85_evidence.txt).
- The tool that rewrote Limelight after export is not identified. ttfautohint (v0.8 source: tattf.c) re-stamps head.modified, and hg 927784141's message says ttfautohint. But ttfautohint without pre-hinting keeps glyph headers and never recomputes head.yMin, while the release's all-point head box (-636) and its 21 all-point glyph boxes look like a fontTools recompile. The metric values' rule is identified; the tool is not.
- Cubic sources are untested: FontForge measured its own quadratic approximation, which may add on-curve points. All 82 offset-mode styles in both tables are quadratic.
- The <=2011 sethhead quirk, where the hhea DESCENDER's mode comes from HheadAOffset, is not modelled. No style in either table has HheadAOffset != HheadDOffset.
- Releases without FFTM (Play, Tuffy, Corben, ComicRelief; ConcertOne in another batch) do not get the flag. Their vertical-metric rows (Play, Corben) belong to other units and are unchanged by it.
- FINDINGS.md/VERIFY.md were not written (the harness refuses .md files). Everything is in this result, and the probes and runs are under investigations/next-vmetrics/ uncommitted. Scratch under sfd-reland-scratch/vmetrics/ is disposable: the prototype source is saved as runs/babelfont-proto.diff, the edited Limelight .sfd as runs/limelight-vmetrics-edit.diff plus the sfd_edit.py ops above, and the archive source copies and build dirs are regenerable.

## Rerun

    cd /home/fsanches/compartilhado/gf-source-modernization; V=investigations/next-vmetrics; S=/home/fsanches/compartilhado/sfd-reland-scratch/vmetrics; BFU=/home/fsanches/compartilhado/babelfont-rs-worktrees/integration-ff-prs/target-heights/release/babelfont
    FAMILIES=families-next.tsv BF=$BFU OUT=$V/runs/00-baseline TAG=vmetrics-00-baseline SCRATCH=$S bash tools/baseline.sh Limelight-Regular MountainsofChristmas-Bold NothingYouCouldDo
    git -C /home/fsanches/compartilhado/upstream_repos/repo_archive/googlefonts/googlefontdirectory-hg.git show 52f780bc9d197280a9f430574e179a5f233c56b6:ofl/limelight/src/Limelight-Regular-TTF.sfd > $S/edits/Limelight-Regular-TTF.vmetrics.sfd; for a in 'OS2TypoAscent 1864' 'OS2TypoAOffset 0' 'OS2WinAscent 1864' 'OS2WinAOffset 0' 'OS2WinDescent 629' 'OS2WinDOffset 0' 'HheadAscent 1864' 'HheadAOffset 0' 'HheadDescent -629' 'HheadDOffset 0'; do $PY tools/sfd_edit.py $S/edits/Limelight-Regular-TTF.vmetrics.sfd setfield "$a"; done
    FAMILIES=families-next.tsv BF=$BFU OUT=$V/runs/01-limelight-sfd-edit TAG=vmetrics-01-limelight-sfd-edit SCRATCH=$S SRC_OVERRIDE=$S/edits/Limelight-Regular-TTF.vmetrics.sfd bash tools/baseline.sh Limelight-Regular
    (prototype) git clone --branch integration-ff-prs /home/fsanches/compartilhado/babelfont-rs-worktrees/integration-ff-prs $S/babelfont-proto && git -C $S/babelfont-proto apply $V/runs/babelfont-proto.diff && sudo -n /usr/local/sbin/drop-caches; cd $S/babelfont-proto && CARGO_BUILD_JOBS=3 CARGO_TARGET_DIR=$S/target cargo build --release -p babelfont --features cli
    FAMILIES=families-next.tsv BF=$V/probes/bf_first.sh EXTRA_FLAGS=--fontforge-legacy-offset-metrics OUT=$V/runs/02-legacy-offset-metrics TAG=vmetrics-02-legacy-offset-metrics SCRATCH=$S bash tools/baseline.sh MountainsofChristmas-Bold NothingYouCouldDo MountainsofChristmas-Regular
    bash $V/probes/workaround_regate.sh MountainsofChristmas-Bold $S/baseline/MountainsofChristmas-Bold-vmetrics-02-legacy-offset-metrics $V/runs/03-legacy-offset-metrics+workarounds
    FAMILIES=families-next.tsv BF=$V/probes/bf_first.sh EXTRA_FLAGS=--fontforge-legacy-offset-metrics OUT=$V/runs/04-limelight-edit+legacy-offset-metrics TAG=vmetrics-04 SCRATCH=$S SRC_OVERRIDE=$S/edits/Limelight-Regular-TTF.vmetrics.sfd bash tools/baseline.sh Limelight-Regular
    FAMILIES=families.tsv BF=$BFU OUT=$V/runs/05-unifraktur-before TAG=vmetrics-05 SCRATCH=$S bash tools/baseline.sh UnifrakturMaguntia-Book; FAMILIES=families.tsv BF=$V/probes/bf_first.sh EXTRA_FLAGS=--fontforge-legacy-offset-metrics OUT=$V/runs/06-unifraktur-legacy-offset-metrics TAG=vmetrics-06 SCRATCH=$S bash tools/baseline.sh UnifrakturMaguntia-Book
    $PY $V/probes/offset_bases_sweep.py > $V/runs/offset_bases_sweep.txt
    $PY $V/probes/proto_metrics_sweep.py > $V/runs/proto_metrics_sweep.txt
    $PY $V/probes/limelight_release_edit.py > $V/runs/limelight_release_edit.txt
    for f in copse daysone handlee giveyouglory concertone: $PY $V/probes/offset_bases_sweep.py --sfd <hg 52f780bc ofl/$f/src/*-TTF.sfd> <google/fonts ofl/$f/*.ttf>  (runs/offset_bases_pr85_evidence.txt)
    cd $S/babelfont-proto && cargo fmt -p babelfont -- --check && CARGO_BUILD_JOBS=3 CARGO_TARGET_DIR=$S/target-clippy cargo clippy -p babelfont --features cli --all-targets -- -D warnings && CARGO_TARGET_DIR=$S/target cargo test --release -p babelfont --lib   (runs/babelfont-proto-checks.txt)
