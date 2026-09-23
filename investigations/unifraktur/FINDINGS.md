# unifraktur -- investigation findings

**Model**: Claude Opus 5.5 (investigating agent, adversarial verifier, and the
conclusion below). Written from the agents' structured results (`results.json`).

## Conclusion

Seven rows, every one reproduced from the unmodified source with the FontForge build the
release's FFTM names. The cap height is the pre-2012 height rule (converter). The hhea and
win descents are FontForge's exporter bases for offset-mode metrics -- win from the
on-curve-only head bbox, hhea from int() of the true bounds widened to the head bbox -- a
converter change NOT yet implemented. The three GPOS rows are FontForge's empty GPOS, which
shares GSUB's script list when only GSUB has lookups. It is functional: HarfBuzz skips its
fallback mark positioning when a GPOS exists, and adding the shell to our build takes
shaping from 648 differing runs to 0. Under the equivalence rule (2026-09-24: reproduce
what ships, improve in later commits) it must be reproduced; FEA cannot express it and
fontc does not emit it, so it needs a tool change. Not landed.
The Book/Regular file name is a METADATA.pb files mapping, disclosed as a converter
normalisation.

## Investigator's report

All 7 rows are converter-fidelity. The release is what FontForge (build of 2010-04-29,
commit cd438ca99d76) exports from this unmodified .sfd; FFTM sourceModified equals the
.sfd's ModificationTime. (1) Empty GPOS: FontForge deliberately shares GSUB's script
list into GPOS for Uniscribe. It matters here because HarfBuzz turns off fallback mark
positioning when a GPOS exists. Adding the shell makes horizontal shaping identical to
the release. FEA and fontc cannot emit it; it needs a compiler or build step. (2)
Vertical metrics: the .sfd states offsets (OS2WinDOffset/HheadDOffset 1). FontForge's
bases are the head bbox of on-curve points only (floor -496, from J's implied point
-495.5) for win, and the truncated true curve minimum (-497) for hhea, giving 512/-513.
babelfont rounds the true minimum (-498) and gets 514/-514. (3) Cap height 1409 comes
from FontForge's pre-2012-05-14 bug of dividing the sum of distinct tops by the glyph
count (36635.1/26). The x-height (1095) matches both rules. (4) File name: generate.py
builds it as FontName + '-' + Weight ('UnifrakturMaguntia-Book.ttf'). FontForge's
_GetModifiers falls back to 'Weight: Book' for nameID 2. babelfont names the master and
instance 'Regular' from TTFWeight 400, so builder3 writes UnifrakturMaguntia-
Regular.ttf. That is a METADATA.pb files-mapping matter (filename, post_script_name and
full_name follow the built font, and the PostScript-name change is disclosed), not a
source edit; the gate accepts name records. FINDINGS.md was NOT written: the harness
refused report files from this subagent. Probes, excerpts and run outputs are under
/home/fsanches/compartilhado/sfd-reland/investigations/unifraktur/. Pins: babelfont
binary f725e6a (sha256 f96e0851..., built before ca43adc), gftools-builder3 e851b8b
(fontc 1.0.0), diffenator3 1.1.4, table_gate.py sfd-batch5 cd4f827 (sha256 008e7319...),
sweep.py sha256 75b4d351, fontTools 4.61.1, uharfbuzz 0.53.3 / HarfBuzz 12.3.2,
google/fonts b5efa9c32e8f.

Rows before: 7 (runs/00-baseline, which reproduces baseline/UnifrakturMaguntia-Book.gate.txt): GPOS.script_list, GPOS.feature_list, GPOS.lookup_list, hhea.descender [-513,-514], OS/2.us_win_descent [512,514], OS/2.sx_height [1095,500], OS/2.s_cap_height [1409,700]

Rows after: 0 in a stand-in only: absolute win/hhea descents plus stated heights in a scratch copy of the .sfd (runs/03, 3 rows left, all GPOS) plus FontForge's shared-script GPOS added after the build (gate-graft.txt: '0 blocking table difference(s), 3 stale in the release', no glyph or word differences). The unmodified source still gates 7 until the three converter changes land. The stand-ins are not proposed .sfd edits.

Confidence: high: every value is reproduced exactly from the unmodified source using the FontForge code at the commit that matches the release's FFTM timestamp, and the stand-in builds take the gate to 0 blocking rows. Medium only for how the converter or compiler should implement the GPOS shell.

## Rows

| style | row | class | cause |
|---|---|---|---|
| UnifrakturMaguntia-Book | GPOS.script_list | converter-fidelity | FontForge's exporter shares one script list between GSUB and GPOS. SFScriptsInLookups (lookups.c:298 at cd438ca99d76) ignores its gpos argument, and dumpg___info (tottfgpos.c:3043-3056) still writes a table that has scripts but no lookups; the code comment says this is 'to get around a bug in Uniscribe'. The .sfd has only GSUB lookups (DFLT/hani/latn), so FontForge wrote a GPOS with those 3 scripts. fontc writes none. This was deliberate in FontForge, not a build artefact, which corrects sfd-batch6/UNIFRAKTURMAGUNTIA-EMPTY-GPOS.md. |
| UnifrakturMaguntia-Book | GPOS.feature_list | converter-fidelity | Same as GPOS.script_list: FontForge's shared-script GPOS shell, which carries 0 features. |
| UnifrakturMaguntia-Book | GPOS.lookup_list | converter-fidelity | Same as GPOS.script_list: FontForge's shared-script GPOS shell, which carries 0 lookups. |
| UnifrakturMaguntia-Book | hhea.descender | converter-fidelity | The .sfd gives 'HheadDescent: -16' with 'HheadDOffset: 1', which is an OFFSET, not a value. FontForge's sethhead (tottf.c:2841-2880 at cd438ca99d76) builds the base from int ymin, which is C truncation of the true curve minimum from SplineCharLayerFindBounds. It then widens that to head.yMin. Glyph J's true minimum is -497.5805, which truncates to -497, so FontForge wrote -497-16=-513. babelfont f725e6a (resolve_offset_metrics) uses round(-497.58)=-498 instead and gets -514. |
| UnifrakturMaguntia-Book | OS/2.us_win_descent | converter-fidelity | The .sfd gives 'OS2WinDescent: 16' with 'OS2WinDOffset: 1', which is an offset. FontForge's WinBB (tottf.c:3269-3289) uses base -head.yMin. head.yMin is floor(SplineSetQuickBounds) of the exported contours, and before fontforge ee15007274e9 (2014-09-16) QuickBounds counts only ON-CURVE points, including the implied on-curve points a quadratic .sfd writes with flag 128. J's lowest on-curve point is implied at -495.5, which floors to -496, so FontForge wrote 496+16=512. babelfont uses -round(true min)=498 and gets 514. |
| UnifrakturMaguntia-Book | OS/2.sx_height | converter-fidelity | Being fixed at the converter by someone else. The pinned babelfont f725e6a does not fill the x-height (500 is fontc's default). FontForge's SFStandardHeight gives 1095 under both the master rule and the pre-2012 rule, because all 17 x-height tops are distinct. |
| UnifrakturMaguntia-Book | OS/2.s_cap_height | converter-fidelity | The release was exported by a FontForge older than commit 4d34d21ef866 (2012-05-14, Khaled Hosny's patch 'it was dividing by the wrong value'). When no top is flat, the old SFStandardHeight (splinefont.c:1702-1706 at cd438ca99d76) does 'test += curves[i].pos; tot += curves[i].cnt;': it adds up the DISTINCT tops and divides by the number of GLYPHS. None of the A-Z tops is flat and I and J share 1503.094, so the result is 36635.1/26 = 1409.04, truncated to 1409. The oracle ports FontForge master, which divides by the distinct count (25) and gets 1465.40 -> 1465. |

## Proposed converter changes

- Offset-mode vertical metrics: use FontForge's exporter bases (babelfont fontforge.rs resolve_offset_metrics, and its inverse offsetmetrics.rs compute_offset_delta). (1) Win base = FontForge's head bbox: per glyph, floor(min)/ceil(max) of the ON-CURVE points of the exported contours, counting implied quadratic on-curve points (flag 128) and resolved references. Off-curve points count only for an exporter from fontforge ee15007274e9 (2014-09-16) or later. winDescent = -head.yMin + offset, winAscent = head.yMax + offset. (2) hhea base = C truncation toward zero of the true curve bounds (SplineCharLayerFindBounds), widened to that head bbox. Today babelfont applies round() of the true bounds to both. Quirk to reproduce: FontForge <= 2012 decides the hhea DESCENDER mode from hheadascent_add (tottf.c:2876); master uses hheaddescent_add. Cubic sources are untested: FontForge measures its own quadratic approximation (SSttfApprox), and every offset-mode style in families.tsv is quadratic.

  Evidence: vmetrics_probe.py gives win 512 and hhea -513 under the FontForge <= 2014 rule, equal to the release; babelfont gives 514/-514. vmetrics_sweep.py over families.tsv (60 offset-mode metrics in 15 styles): FontForge rule 41 matches, babelfont 39; the only difference is these 2 rows, with no regressions. Scratch stand-in with absolute values: 7 -> 5 rows (runs/02-proxy-vmetrics). The quoted code is in ff-2010-excerpts.txt.
- x-height/cap-height for exporters before 2012-05-14: give fontforge_standard_height.rs (ca43adc, another person's work) a switch. When no top is flat, the curve mean then divides by the GLYPH count (sum of counts) instead of the number of distinct heights, reproducing FontForge before 4d34d21ef866. The flag is chosen per release, the same way baseline.sh already asks the release: turn it on when the release's FFTM FFTimeStamp is before 2012-05-14.

  Evidence: heights_pre2012_probe.py: 31 of 38 releases reproduced vs 25 of 38 with the master rule. The six added styles all have FFTM builds from 2010-04-29 or 2011-02-22, and none is lost. PatrickHand (FFTM 2012-09-06, after the fix) is unaffected. For this style: cap height 1409 (release 1409) vs 1465; x-height 1095 under both.
- FontForge's shared script list: when the source has lookups in only one of GSUB and GPOS, emit the other table with the same scripts and languages (empty default LangSys) and 0 features / 0 lookups, as FontForge's SFScriptsInLookups + dumpg___info did. The .glyphs format and FEA cannot express this, so babelfont alone cannot do it. It needs a fontc option or a gftools-builder3 post-compile step in the recipe, keyed to FontForge-exported releases.

  Evidence: empty_gpos_probe.py adds this shell to our build: the 3 GPOS rows close, no other row opens, and horizontal HarfBuzz shaping goes from 648 differing runs to 0 of the ltr/rtl share of 25008. fea_empty_feature_test.sh shows an empty 'feature kern {} kern;' makes fontc 1.0.0 emit no GPOS. In families.tsv, 23 releases carry FontForge's shell (19 with an empty GSUB, 4 with an empty GPOS). Only this one blocks, because it is the only style with combining marks; the table_gate _nothing_to_position guard passes the rest.

## Unresolved

- FINDINGS.md was not written: the harness blocked report .md files from this subagent. The content is in this result, and the probes and runs are in the investigations dir. The parent needs to write FINDINGS.md from it if it wants the file.
- The GPOS shell cannot be closed through babelfont or FEA. Someone has to pick the mechanism: a fontc option, a gftools-builder3 recipe post-step, or leaving the rows open. That decision belongs to Felipe or the tool owners.
- sfd-batch6/UNIFRAKTURMAGUNTIA-EMPTY-GPOS.md says the empty GPOS 'looks like a build artefact rather than a decision'. FontForge's source shows it was deliberate (Uniscribe script sharing). That text needs correcting, and this unit may not edit it.
- Not among the 7 rows: GDEF is marked RELEASE-STALE. FontForge 2010's gdefclass makes these 9 combining marks base glyphs because the .sfd has no anchors and no GlyphClass. Our build classes them as marks, which is a correction made silently in the converter/compiler rather than a visible .sfd edit. It is inert for horizontal shaping once the GPOS shell exists.
- Vertical text (ttb/btt) still differs in 6225 runs per direction even with every row closed. HarfBuzz's fallback vertical origin reads the per-glyph glyf header bbox, and the release keeps FontForge's on-curve-only headers. The gate does not check this.
- The offset-base rule is proven for quadratic sources only. For cubic sources FontForge measures its own quadratic approximation (SSttfApprox), which no offset-mode style in families.tsv exercises.

## Rerun

    cd /home/fsanches/compartilhado/sfd-reland && TAG=unifraktur OUT=/home/fsanches/compartilhado/sfd-reland/investigations/unifraktur/runs/00-baseline bash tools/baseline.sh UnifrakturMaguntia-Book
    TAG=unifraktur OUT=.../runs/02-proxy-vmetrics SRC_OVERRIDE=<copy of the .sfd patched with runs/02-proxy-vmetrics/source.diff> bash tools/baseline.sh UnifrakturMaguntia-Book
    TAG=unifraktur OUT=.../runs/03-proxy-vmetrics-heights SRC_OVERRIDE=<copy patched with runs/03-proxy-vmetrics-heights/source.diff> bash tools/baseline.sh UnifrakturMaguntia-Book
    /home/fsanches/compartilhado/gftools/venv/bin/python3 investigations/unifraktur/empty_gpos_probe.py <release.ttf> runs/03-proxy-vmetrics-heights/UnifrakturMaguntia-Regular.ttf runs/03-proxy-vmetrics-heights/UnifrakturMaguntia-Regular+ffgpos.ttf; then diffenator3 -J 1 --no-languages --no-match --json --succinct <release> <out> and table_gate.py <json> --fonts <release> <out>
    $PY investigations/unifraktur/vmetrics_probe.py <UnifrakturMaguntia.sfd from hg 52f780bc> <release.ttf>
    $PY investigations/unifraktur/vmetrics_sweep.py
    $PY investigations/unifraktur/heights_pre2012_probe.py
    bash investigations/unifraktur/fea_empty_feature_test.sh runs/00-baseline/UnifrakturMaguntia-Book.glyphs <scratch dir>
