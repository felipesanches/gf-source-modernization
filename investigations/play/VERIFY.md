# play -- adversarial verification

**Model**: Claude Opus 5.5. Written from the verifier's structured result.

Reproduced: True

No .sfd edits were proposed, so I verified by rerunning the baseline from the unmodified
sources: SCRATCH=.../scratchpad/inv-play-verify TAG=play-verify OUT=.../inv-play-
verify/runs/baseline bash sfd-reland/tools/baseline.sh Play-Regular, then the same for
Play-Bold, one at a time. Result: Play-Regular BLOCKING 220 and Play-Bold BLOCKING 233.
The BLOCKING lines and the .tsv rows are identical to sfd-reland/baseline/, so
rows_after = rows_before = 220/233, which confirms their numbers. Pairing is correct:
each build came from its own families.tsv row (hg 52f780bc9d
ofl/play/src/Play-<Style>-TTF.sfd vs google/fonts b5efa9c32e8f
ofl/play/Play-<Style>.ttf). Tool pins: babelfont binary sha256 f96e0851...ff19, built
2026-09-23 20:27:57. The worktree HEAD has since moved to ca43adc, but this binary still
emits sx 500/cap 700, so the heights fix is not in it. Also builder3 e851b8b (embeds
babelfont-rs 6c460e2), diffenator3 1.1.4, table_gate.py sha256 391e296d...f4. I checked
their provenance claims independently from my own fresh mirrors. The release differs
from 3565c8a fonts/ttf/* only in head. Against the f17f03f unhinted export, it differs
only in cvt/fpgm/prep/glyf bytes/loca/maxp/name/head, with 0 glyphs differing in
coordinates, flags or endpoints. The name ID 3 is '2.101;PLAY;Play-Regular', which is
the form Glyphs.app writes. sources/Play.glyphs is blob b5d9f58 at both commits. A
three-way per-codepoint check (release v2.101 / hg v1.002 binary / our build) found: all
133 LOST codepoints are absent from v1.002 too, so no fidelity cause is possible. For
the renamed rows, our build equals v1.002 while the release differs in 63/65 (Regular)
and 77/78 (Bold). In Regular U+044A and U+0457 the .sfd also differs from v1.002. Bold
U+042F has the same advance and bbox as v1.002 and an area 0.15% different. .sfd counts:
Regular 1005 StartChar, 693 Encoding + 1 AltUni = 694; Bold 986, 691 + 3 = 694.
ff_heights_oracle on the play rows gives 484/484 and 649/649 MATCH for both styles. I
reproduced Route A: builder3 e851b8b on the original Glyphs 2 Play.glyphs produced only
Play-Regular.ttf (rc=0, Bold silently missing), the gate gives 62 rows (BLOCKING lines
identical to theirs), and U+07DD maps to endash. Scratch paths: /tmp/claude-1000/-home-
fsanches-compartilhado-GoogleFonts/f55394dc-b840-4055-b5b4-e2463e4b4dd8/scratchpad/inv-
play-verify/{runs/baseline,modern,relcmp.py,os2dump.py,threeway.py,renamed_kind.py}.
VERIFY.md was NOT written: the subagent system rules forbid report .md files (the same
rule that stopped the first agent), so the report is this result. These probes exist
only in volatile scratch and need copying to sfd-reland/investigations/play/verify/ to
survive.

## Verdict

CONFIRMED with minor revisions. What google/fonts ships (ofl/play, e36afc756, v2.101) is
the Glyphs.app export of sources/Play.glyphs (blob b5d9f58), autohinted by
sources/build.sh (ttfautohint -x 13). I checked this table by table and glyph by glyph
against my own mirrors: against 3565c8a it differs only in head, and it matches the
unhinted f17f03f export except in hinting-related tables. The hg .sfd files
(v1.001/v1.002, 2011) lack 133 codepoints and the whole v2 feature code, and 218/231
outlines differ. No FontForge-exporter fidelity rule of any vintage can produce the
missing glyphs or the Glyphs-derived OS/2, hhea, GSUB and GDEF. I checked the 2012 and
master tottf.c/sfd.c handling of the typo and hhea descender, and the sub/superscript
and strikeout values are stated in the .sfd, so --fontforge-os2-defaults does not apply.
The provenance classifications stand; the converter-fidelity classification of heights
and weight class stands. Their 220/233 baseline and the 62-row Route A gate both
reproduced exactly. Their two Route A converter defects are real; the unicode fix needs
retargeting to upstream babelfont-rs 6c460e2, the version builder3 embeds. Main
correction: the canonical upstream is alexeiva/play d84ad58 (same tree as m4rc1e
3565c8a), not the m4rc1e fork. Decision for Felipe: googlefonts/play was created empty
for an SFD re-land, but the SFD route cannot meet the rule, because its final commit
would reproduce v1.002 at best. Play should move to the modern-upstream track: push
alexeiva/play history into googlefonts/play, keep the hg .sfd, the librefonts mirror and
the google/fonts 874c7ceb1 VFB/.glyphs documented as original v1 sources, and correct
the local METADATA.pb commit 51c6a423f and upstream_info.md. VERIFY.md was not written:
the subagent system rules forbid report .md files, so this result is the report. My
probes and mirrors (inv-play-verify/relcmp.py, os2dump.py, threeway.py, renamed_kind.py,
runs/, modern/, alexeiva-play.git, m4rc1e-play.git, librefonts-play.git) are only in
volatile scratch and should be copied into sfd-reland/investigations/play/verify/ and
the repo archive. I committed nothing.

## Per edit

- [keep] (no .sfd edit proposed) -- decision to leave the .sfd untouched -- An edit could only close the scalar rows (vendor, typo/hhea descender, win metrics, sub/sup, strikeout, panose). Three of those would discard values the designer stated in the .sfd: Panose 2 11 0..., OS2Sub*/Sup* 700/650/140/477, and OS2StrikeYPos 250. The cmap (133 codepoints), GSUB/GDEF, hmtx and num_glyphs rows could only close by importing the whole v2 glyph set from the binary. Declining was correct.
- [revise] [converter, Route A] babelfont Glyphs 2 reader: an all-digit 'unicode = NNNN;' is hex -- The defect is real, and I reproduced it: babelfont f725e6a converting Play.glyphs keeps endash 'unicode = 2013;' in its Glyphs 3 output, where it reads as decimal; 50 glyphs are affected (2013..2265); the builder3 e851b8b build maps U+07DD to endash. Revise the attribution: the build did not use f725e6a, it used builder3's embedded babelfont-rs 6c460e2. So the fix belongs in upstream babelfont-rs, followed by a builder3 dependency bump. Also, this matters only for Route A, not for an SFD edit.
- [keep] [converter, Route A] Glyphs 2 instance without interpolationWeight defaults to 100 -- Confirmed. In Play.glyphs the Bold master has no weightValue and the Bold instance has no interpolationWeight. babelfont's Glyphs 3 output gives the master axesValues (100) but the instance (0), and the recipe instantiates wght=0 for Play-Bold.ttf. Also add: builder3 exits 0 while the Bold target is never written, so the failure is silent.

## Objections

- Play-Bold hhea.ascender: the classification (provenance) stands, but the stated mechanism is wrong. With HheadAOffset 1, FontForge writes hhea.ascender = bbox yMax + HheadAscent (0) = 932 (2012 tottf.c ~l.2964-2967). The '800+132' rule they quote is the OS/2 typo ascender rule (tottf.c:3446-3449).
- Their confidence line says 'the .sfd reproduces the 2011 v1.002 binary'. That holds for Bold (9 rows; 0 outline or advance differences) but is overstated for Regular. The Regular .sfd is not the state v1.002 was exported from either: Version 001.001 vs 1.002, OS2Vendor 'PT  ' vs PLAY, typo/hhea descender +220 vs -220, 1005 vs 1007 glyphs, and the U+044A/U+0457 outlines differ from v1.002. FontForge 2012 and master both write a non-offset typo/hhea descender exactly as stored (2012 tottf.c:3450-3453, 2968-2971; sfd.c:6490 getsint), so this is not a fidelity gap. Their v2.101 conclusion does not change.
- The label 'renamed+redrawn' overstates some rows. Bold U+042F has the same advance and bbox as the release, and its area differs by only 0.15%; our build is identical to v1.002 there, so this may be the outline being re-represented in the v2 pipeline rather than redrawn. It is still provenance, because the shipped glyph comes from Play.glyphs. Regular U+0422 (8/8 points, -0.62% area) is a real geometry change.
- sx_height/s_cap_height as converter-fidelity: accepted for the SFD route (v1.002 also has 484/649 and the oracle matches). Note that the v2.101 values actually come from Play.glyphs xHeight 484 / capHeight 649, which happen to equal FontForge's rule. On Route A the question does not arise.
- They name the recommended upstream as m4rc1e/play, but that is a fork. The canonical repo is alexeiva/play (Alexei Vanyashin/Cyreal, the v2 author, who merged m4rc1e PRs #4, #5 and #6). Its tip d84ad58, the merge of PR #6, has tree 57de73f, identical to m4rc1e 3565c8a. Recommend repository alexeiva/play at commit d84ad58, and mirror both; neither is in the repo archive.
- A small error in their unresolved notes: sfd-batch6/progress.tsv shows Play-Regular nglyphs 1007/1150 and Play-Bold 987/1150, not '1005/1150'. Their point, that the 16-row B6-RESIDUALS figure was measured after the cmap/heights copying, still holds.

## Missed

- Canonical upstream alexeiva/play (tip d84ad58, same tree as m4rc1e 3565c8a) was not identified. Their Route A recommendation should name it, and the archive mirror command should be: git clone --mirror https://github.com/alexeiva/play .../repo_archive/alexeiva/play.git (plus m4rc1e/play.git).
- google/fonts history held other Play sources they did not mention. Commit 874c7ceb1 (2016-10-31, Alexei Vanyashin) added ofl/play/Play-{Regular,Bold}.glyphs (XML plist, Glyphs 1 era), Play-{Regular,Bold}.vfb and Play-Bold.vfbak; e36afc756 deleted them. The .vfb files are probably the FontLab design masters. The hg '-TTF.sfd' names suggest the .sfd files were themselves made by opening a TTF in FontForge. Both should be documented as original sources (the preserve-old-repo-info policy).
- librefonts/play (0d4e17b, 2014) holds byte-identical copies of the hg .sfd blobs (873353d, f9e5b94) plus TTX dumps. It adds no new source and is not in the archive.
- Stale local metadata. The google/fonts working copy has commit 51c6a423f (on local branches such as add-legacy-sources-config-overrides, not upstream), which points METADATA.pb at googlefontdirectory-hg 52f780bc9d. Its upstream_info.md (8b0a1d0f5) says 'No canonical upstream GitHub repository was identified'. Both are wrong for v2.101 and must be corrected, or kept out of any pending PR, if Route A is chosen.
- Route A leftovers they left open have likely Glyphs.app-export explanations (not checked against Glyphs.app code). post.underline_position -75 = -100 + 50/2, the underline centre converted to its top, the same convention as FontForge's --fontforge-underline-position and ufo2ft's public.openTypePostUnderlinePosition. panose bWeight 5/8 matches Glyphs.app deriving it from weight class 400/700 (release Regular 5, Bold 8).
- builder3 e851b8b returns rc=0 when the Play-Bold.ttf target is never produced. The failure is silent and should be reported alongside the interpolationWeight defect.
- A cross-family fidelity note (no effect on Play): FontForge's 2012 exporter (e4aa2e0 tottf.c:2968) picks the hhea DEScender offset using the hheadascent_add flag; master fixed this to hheaddescent_add. A .sfd with HheadAOffset != HheadDOffset, reproducing a pre-fix export, would need a converter rule for it.
- Their artefacts: probes/README.md and classify_rows.py refer to a FINDINGS.md that does not exist, and every probe hard-codes the m4rc1e mirror path in volatile scratch.
- Coverage: every blocking row is accounted for. Regular 220 = 133 LOST + 65 renamed + 22 others; Bold 233 = 133 + 78 + 22. Both styles of the family are covered. No edits were applied, so none opened new rows.
