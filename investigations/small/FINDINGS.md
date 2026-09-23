# small -- investigation findings

**Model**: Claude Opus 5.5 (investigating agent, adversarial verifier, and the
conclusion below). Written from the agents' structured results (`results.json`).

## Conclusion

RussoOne: one documented edit, `FSType 0` (google/fonts 8ccda7bf7 fixed the binaries in
2015; the source still states 4). Comic Relief: its underline is FontForge's post-2019 rule,
trunc(position + width/2) (the `.sfd` is SplineFontDB 3.2) -- moot for now, because Comic
Relief has an active upstream and is not being converted.

## Investigator's report

Every run printed its gate summary line and the full rerun.sh reproduced all 7 runs. The
RussoOne edit is verified with the real source edit. The ComicRelief converter rule is
verified only by simulation: babelfont could not be built in this unit. So a copy
stating the rule's output (-97) was converted with the stock converter, and
convert_diffs.sh proved that .glyphs differs from the unmodified conversion only in
underlinePosition. Once the filter lands, rerun without SRC_OVERRIDE to confirm it for
real. FINDINGS.md could not be written: the subagent harness refuses report files. Its
content is in this result and all evidence files exist under
investigations/small/{probes,runs,edits}.

Rows before: Baseline (f725e6a): ComicRelief-Regular 1 (post.underline_position [-97,-272]); ComicRelief-Bold 2 (OS/2.us_weight_class [700,400], post.underline_position [-97,-272]); RussoOne-Regular 2 (OS/2.fs_type [0,4], OS/2.sx_height [530,500]); Tuffy-Regular/Italic fs_type [8,0] (reported only, not rerun).

Rows after: RussoOne-Regular with FSType 0: 1 at f725e6a (sx_height only), 0 at ca43adc (CLEAN). ComicRelief-Regular with the simulated rule output (-97): 0 (CLEAN). ComicRelief-Bold with the simulated rule: 1 (us_weight_class only, fontc in progress). No new BLOCKING rows; RELEASE-STALE lists are unchanged against baseline/*.gate.txt. Every run printed its closing 'N blocking table difference(s)' line.

Confidence: high: RussoOne fsType (verified edit, clear history) and the Comic Relief underline root cause (the release's own toolchain was executed and reproduces -97 exactly). medium-high: the converter filter's gate outcome, which is verified by exact simulation, not by the implemented filter.

## Rows

| style | row | class | cause |
|---|---|---|---|
| ComicRelief-Regular | post.underline_position [-97, -272] | converter-fidelity | The release was not exported by FontForge. It was built by the repo's own pipeline at 856315f (= tag v1.2): sfdLib 2.0.0.post0 sfd2ufo, then gftools builder 0.9.77 / ufo2ft 3.4.1. sfdLib converts the .sfd's UnderlinePosition (the centre) to the top with postscriptUnderlinePosition += thickness/2 (-185 + 87.5 = -97.5). ufo2ft then writes otRound(-97.5) = -97. babelfont's --fontforge-underline-position applies FontForge's pre-2019 rule trunc(pos - width/2) = -272. Without the flag, babelfont carries the raw -185. No existing flag produces -97. |
| ComicRelief-Bold | post.underline_position [-97, -272] | converter-fidelity | Same as Regular: identical UnderlinePosition -185 / UnderlineWidth 175, identical toolchain (sfdLib sfd2ufo + ufo2ft otRound of pos + width/2 = -97). |
| ComicRelief-Bold | OS/2.us_weight_class [700, 400] | converter-fidelity | Converter work in progress: fontc 1.0.0 ignores a single-master Glyphs instance's weightClass (issues/fontc-static-weight-class.md). The .sfd states TTFWeight: 700, and the converted .glyphs instance says weightClass = 700. |
| RussoOne-Regular | OS/2.fs_type [0, 4] | source-edit-from-release | The .sfd states FSType: 4, and the binary FontForge exported from it carried 4. google/fonts 8ccda7bf7 (2015-08-05, Dave Crossland, 'Fix fsType for 40 font files') changed the shipped binary to 0 after export. The value 0 exists only in the release. |
| RussoOne-Regular | OS/2.sx_height [530, 500] | converter-fidelity | Converter work in progress: FontForge's exporter computes sxHeight (SFStandardHeight). The f725e6a converter lacks the port, and ca43adc has it. |
| Tuffy-Regular | OS/2.fs_type [8, 0] | provenance | Report only; the tuffy unit owns the rest. The source states FSType: 0 in both Tuffy-Regular-TTF.sfd (the families.tsv source) and Tuffy-Regular.sfd. The shipped 8 first appears in the v1.272 rebuild, google/fonts ebcdfd2bb (2017-10-24, Micah Stupak, 'v 1.272 added. Fixes ots failure. (#1269)'). That binary has no FFTM, while the source says Version 001.271. The release was not built from this source state. Reproducing it would take setfield FSType 8 (source-edit-from-release), which adds a DRM bit the source does not state. This was not tested here. |
| Tuffy-Italic | OS/2.fs_type [8, 0] | provenance | Same as Tuffy-Regular (report only). The source (-TTF.sfd and plain .sfd) states FSType: 0. The release's 8 was introduced by the v1.272 rebuild in google/fonts ebcdfd2bb (2017-10-24), which was not exported by FontForge. |

## Proposed .sfd edits

- **FSType 0** (RussoOne-Regular) `setfield FSType 0` -- verified: True; value from: The release only. google/fonts 8ccda7bf7 changed the shipped RussoOne-Regular.ttf from fsType 4 to 0 after export (40 fonts in that commit: 34 at 4, all ended at 0). Neither the source nor the FontForge-exported hg-era binary states 0.; the source stated: FSType: 4 (line 18 of googlefontdirectory-hg 52f780bc9d19 ofl/russoone/src/RussoOne-Regular-TTF.sfd)

## Proposed converter changes

- New opt-in babelfont filter, suggested name --underline-position-centre-to-top (the name is Felipe's call). For each master it sets UnderlinePosition := otRound(position + thickness/2), in i32 as (2*position + thickness + 1).div_euclid(2), with missing thickness = 0. It must be mutually exclusive with --fontforge-underline-position, which is the pre-2019 rule trunc(position - thickness/2). The rule is sfdLib sfd2ufo + ufo2ft; FontForge >= 20190317 (tottf.c:4089 putshort(upos+uwidth/2), which truncates) gives the same value whenever position + thickness/2 <= 0. WARNING: the naive integer form position + thickness/2 gives -98 for Comic Relief (175/2 = 87), not -97. Suggested tests: -185/175 -> -97; -50/50 -> -25; applying twice is not the same as once. Help text should state only the format rule (centre -> top, + half thickness, rounded half up).

  Evidence: ComicRelief .sfd: UnderlinePosition -185, UnderlineWidth 175; the release has -97. The release toolchain was sfdLib 2.0.0.post0 (parser.py:1557-1558: postscriptUnderlinePosition += thickness/2) and ufo2ft 3.4.1 (outlineCompiler.py:956 otRound). Executed end to end, it reproduces -97 for both styles (probes/sfdlib_underline.sh -> runs/sfdlib_underline.txt). Simulated through the real pipeline, the gate goes Regular 1 -> 0 and Bold 2 -> 1, with no new rows (runs/comicrelief-*-sim97). The .glyphs differ from the unmodified conversion only in underlinePosition (runs/convert_diffs.txt). Only these 2 of 42 styles need it (runs/underline_rules.txt).

## Unresolved

- The ComicRelief converter filter is specified but not implemented or built (babelfont builds were out of scope). Verification is by exact simulation. After the filter lands, rerun baseline.sh for ComicRelief-{Regular,Bold} with the new flag and without SRC_OVERRIDE.
- Filter name and CLI shape are suggestions: a new flag vs a value on --fontforge-underline-position. tools/recipe.py and baseline.sh need a per-family override for comicrelief; today both apply --fontforge-underline-position to every style.
- Tuffy-Regular/Italic fs_type: the source states 0 and the v1.272 release (ebcdfd2bb, 2017) states 8. Whether to reproduce 8 (setfield FSType 8, adding a DRM bit the source does not state) is for the tuffy unit / Felipe. Not tested here.
- The release's ufo2ft was 3.4.1. The probe executed ufo2ft 3.7.0 from the gftools venv. The underline code is the same in 3.4.1, but that was read from its PyPI wheel, not executed.
- FINDINGS.md not written: the harness blocked report files. The orchestrator should write it from this result.

## Rerun

    sh /home/fsanches/compartilhado/sfd-reland/investigations/small/probes/rerun.sh   # everything below, in order, one build at a time
    sh probes/make_edits.sh   # regenerates edits/*.sfd from the archive via tools/sfd_edit.py
    cd /home/fsanches/compartilhado/sfd-reland && TAG=small OUT=investigations/small/runs/russoone-fstype0 SRC_OVERRIDE=investigations/small/edits/RussoOne-Regular-TTF.fstype0.sfd bash tools/baseline.sh RussoOne-Regular
    BF=/home/fsanches/compartilhado/babelfont-rs-worktrees/gf-sfd-conversion/target-heights/release/babelfont TAG=small OUT=investigations/small/runs/russoone-fstype0-ca43adc SRC_OVERRIDE=investigations/small/edits/RussoOne-Regular-TTF.fstype0.sfd bash tools/baseline.sh RussoOne-Regular
    BF=<ca43adc> TAG=small OUT=investigations/small/runs/russoone-unmodified-ca43adc bash tools/baseline.sh RussoOne-Regular
    DROP_FLAGS=--fontforge-underline-position TAG=small OUT=investigations/small/runs/comicrelief-{regular,bold}-noflag bash tools/baseline.sh ComicRelief-{Regular,Bold}
    DROP_FLAGS=--fontforge-underline-position TAG=small OUT=investigations/small/runs/comicrelief-{regular,bold}-sim97 SRC_OVERRIDE=investigations/small/edits/ComicRelief-{Regular,Bold}.upos-sim-97.sfd bash tools/baseline.sh ComicRelief-{Regular,Bold}
    sh probes/sfdlib_underline.sh; python3 probes/underline_rules.py; python3 probes/release_facts.py; sh probes/convert_diffs.sh [babelfont]
