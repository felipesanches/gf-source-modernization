# tuffy -- investigation findings

**Model**: Claude Opus 5.5 (investigating agent, adversarial verifier, and the
conclusion below). Written from the agents' structured results (`results.json`).

## Conclusion

Tuffy-Bold and BoldItalic are FontForge 2.0 exports of exactly these `.sfd`. Tuffy-Regular
and Italic ship v1.272, a 2017 third-party rebuild (google/fonts PR #1269) of FontForge's
001.271 export, with the traits of a Glyphs.app round trip. Reproducing v1.272 needs a
dozen edits that commit its defects -- 43 Greek iota-subscript glyphs drawn beside rather
than under the letter, fsType 8, 500/700 heights that are Glyphs defaults, not the
design's -- and still leaves 3 GSUB rows per style. The alternative is to land against the
001.271 binary Google Fonts shipped 2015-2017, which our build reproduces at 3 rows.
Settled 2026-09-24 by the equivalence rule: the target is v1.272, what ships; its defects
are reproduced and their fixes are future work. Before it can land: v1.272's GSUB (its 11
lookups replacing the source's 4), the verifier's 4 further composite placements, and the
.notdef. Not landed. Two findings
outlived the family: the table gate's area-measure bug (fixed, sfd-batch5 cd4f827) and
FontForge's synthesised `.notdef` (a proposed converter filter).

## Investigator's report

PROVENANCE. Bold/BoldItalic ship FontForge 2.0 exports of exactly these .sfd states
(sha1 == monorepo 52f780b ofl/tuffy/*.ttf; FFTM sourceModified == .sfd ModificationTime
to the second). Regular/Italic ship v1.272, made in 2017 by a third party (google/fonts
ebcdfd2bb, PR #1269, 'fixed ots errors and ttfautohinted') FROM FontForge's 001.271
export of these .sfd states -- which is byte-identical to what google/fonts shipped
2015-03..2017-10 (sha1 c0ec1c8d/b62df32a) and which our build reproduces at 3 rows (GSUB
liga lookup order with 0/336 shaping differences, head.font_direction_hint 0 vs 2; per
codepoint 2 and 0 glyphs differ). v1.272 kept head.created from that TTF, matches its
bboxes (never the .otf's alone), but has no FFTM, OS/2 v3 with unscaled 500/700 heights,
name 3 '1.272;PfEd;Tuffy-Regular', ttfautohint 1.6, overlaps removed, curves refit with
extrema, components re-aligned automatically and a GSUB regenerated from glyph names --
consistent with a Glyphs.app round trip (inference). The source STATES corrupt OS/2
sub/super/strike values (-25944 etc.) that FontForge exported verbatim and OTS flags;
this contradicts B6-RESIDUALS line 65 for Regular/Italic. CLOSURE vs v1.272: all rows
except GSUB close by verified edits (FSType, 10 OS/2 fields, 2 encodings, 12 composite
placements in Regular incl. the 6 iota-subscript bases that fix 43 Greek rows, U+032E as
zero-width mark, imported outlines for 2/11 glyphs), one converter change (FontForge's
synthesised .notdef, emulated) and one gate fix (area measure). FORWARD WARNING:
babelfont ca43adc's heights fill opens sx_height [500,1069] and s_cap_height [700,1450]
on Regular/Italic; addfield OS2XHeight 500 / OS2CapHeight 700 closes them (verified with
target-heights). DECISION for Felipe: reproducing v1.272 commits its defects (43
displaced Greek iota-subscript glyphs, fsType 8, a GSUB that drops default f+accented-i
ligatures) and still leaves 3 GSUB rows per style; the alternative is to treat
Regular/Italic as provenance and land 001.271. FINDINGS.md was NOT written: the harness
refused report-file writes for subagents; this structured result carries its content.
Probes (each docstring states its question) and all run outputs are under
/home/fsanches/compartilhado/sfd-reland/investigations/tuffy/{probes,edits,runs}.
Nothing committed.

Rows before: Tuffy-Regular 74, Tuffy-Italic 27, Tuffy-Bold 1, Tuffy-BoldItalic 1 (baseline reproduced exactly in runs/r0-baseline)

Rows after: Tuffy-Regular 13 with all proposed .sfd edits + .notdef emulation (3 with the gate fix: GSUB x3); Tuffy-Italic 6 (3 with the gate fix: GSUB x3); Tuffy-Bold 1 and Tuffy-BoldItalic 1 (us_weight_class, converter in progress). No stage opened a row.

Confidence: High on provenance (byte-identity, FFTM timestamps, google/fonts history) and on every edit marked verified: each was applied to a copy of the source and gated with baseline.sh, closing its rows without opening any. Medium on attributing v1.272 to Glyphs.app specifically: that rests on toolchain traits, not on a record. High on the gate area-measure defect: reproduced per glyph and checked against the Allerta control.

## Rows

| style | row | class | cause |
|---|---|---|---|
| Tuffy-Bold, Tuffy-BoldItalic | OS/2.us_weight_class [700, 400] | converter-fidelity | fontc does not set usWeightClass for a static single-master source; the .sfd states TTFWeight: 700. Converter fix in progress elsewhere. Releases are FontForge 2.0 exports of exactly these .sfd states. |
| Tuffy-Regular, Tuffy-Italic | OS/2.fs_type [8, 0] | source-edit-from-release | v1.272 (2017 re-export, google/fonts ebcdfd2bb) sets fsType 8; the .sfd states FSType: 0 and the 001.271 FontForge export carries 0. |
| Tuffy-Regular, Tuffy-Italic | OS/2.y_subscript_x_size, y_subscript_y_size, y_subscript_x_offset, y_subscript_y_offset, y_superscript_x_size, y_superscript_y_size, y_superscript_x_offset, y_superscript_y_offset, y_strikeout_size, y_strikeout_position (10 rows) | source-edit-from-release | The .sfd STATES corrupt values (OS2SubXSize 0, OS2SubYSize 2, OS2SubXOff -16560, OS2SubYOff 0, OS2SupXSize -25944, OS2SupYSize -27176, OS2SupXOff -16376, OS2SupYOff 1, OS2StrikeYSize 12312, OS2StrikeYPos -16224). FontForge's 001.271 export and our build carry them verbatim (so --fontforge-os2-defaults is irrelevant here); OTS 9.2.0 flags 'Bad ySuperscriptXSize: -25944' on both, not on v1.272 -- very likely the 2017 'ots failure'. v1.272 carries 1331/1228/0/153, 1331/1228/0/716, 50/300 (Italic x-offsets -32/150). |
| Tuffy-Regular, Tuffy-Italic | cmap U+0000 LOST [uni0000, null]; cmap U+000D LOST [uni000D, null] | source-edit-from-release | The .sfd has .null (Encoding: 65536 -1 194, width 0) and nonmarkingreturn (Encoding: 65537 -1 195, width 682) unencoded; v1.272 maps them at U+0000/U+000D as uni0000/uni000D. |
| Tuffy-Regular, Tuffy-Italic | hmtx.7 -- the .notdef member (release 748/lsb 68, ours 1024/lsb 102) | converter-fidelity | Regular/Italic .sfd have no .notdef; FontForge's TTF exporter synthesises one (tottf.c dumpmissingglyph: stem 68 because StdVW '[70]' strtod-parses to 0 -> (a+d)/30; advance 748). The 001.271 export has it, v1.272 kept it; fontc synthesises its own 1024-wide glyph. |
| Tuffy-Regular | hmtx.7 -- Agrave, Aacute, Amacron, Iacute, eacute, uacute (widest uacute 120 vs 162) | source-edit-from-release | v1.272 re-aligned the base component to x=0 (source: A -8, I 10, e 10, u 42), as automatic component alignment does. |
| Tuffy-Italic | hmtx.7 -- J, Jcircumflex, periodcentered, uni2076, uni2086, uni20B7 (lsb +1) | source-edit-from-release | v1.272 refit these outlines with extremum points (J 21 -> 25 points), so the curve extremum, not the off-curve control, sets xMin (+1 unit). |
| Tuffy-Regular | cmap U+1F80-1F8F, U+1F98-1F9F, U+1FA0-1FA7, U+1FB2, U+1FB3, U+1FB4, U+1FB7, U+1FBC, U+1FC3, U+1FCC, U+1FF3, U+1FF4, U+1FF7, U+1FFC (43 rows) | source-edit-from-release | v1.272 re-laid out the six iota-subscript base composites (iotasubscript at 0, letter at +801 = iota advance, advance +801) and the 37 composites built on them follow; the iota now sits beside the letter and the letter overflows its advance. Values exist only in the release (a visible defect). |
| Tuffy-Regular, Tuffy-Italic | cmap U+032E [uni032E, brevesubnosp]; GDEF.glyph_classes (only the release marks U+032E) | source-edit-from-release | brevesubnosp ('no spacing') has Width 1302 in the .sfd; v1.272 ships it zero-width, outline moved left by 1302, class mark; in Regular uni1E2A/uni1E2B moved their reference right by 1302 so they draw as before. |
| Tuffy-Regular | cmap U+0162 [uni0162, Tcommaaccent]; cmap U+0163 [uni0163, tcommaaccent] | source-edit-from-release | v1.272 removed the overlap between T/t and its comma (2 contours -> 1): area 1.88%/3.58% vs ours, 0.01%/0.02% after removing overlaps from ours. |
| Tuffy-Italic | cmap U+0162, U+0163, U+E257 (overlap); cmap U+03A9, U+1F6B (refit) | source-edit-from-release | v1.272 removed overlaps (T/t comma, aogonekalt: 1.81/3.60/0.50% -> 0.01-0.02% after overlap removal) and refit Omega/Omegaaspergrave (area 0.41%/0.44% vs ours, just over the gate's 0.4%; the release is 0.34% off FontForge's own export, ours 0.075%). |
| Tuffy-Regular | cmap U+0430, U+0440, U+0458, U+04D1, U+04D3, U+1E03, U+1E0B, U+1E57, U+1FE4, U+1FE5 | gate-arbitration | table_gate._abs_contour_area starts a new contour only on moveTo; a TrueType contour of only off-curve points is drawn as qCurveTo(..., None) with no moveTo, so its area is folded into the previous contour (Cyrillic a: 23.25% 'difference' for drawings 0.15% apart). Same advance, same bbox, area within 0.02-0.15% when split at closePath. |
| Tuffy-Italic | cmap U+0458, U+1E57, U+1FED | gate-arbitration | Same gate area-measure defect (9.98%/4.25%/23.62% under the gate's measure; 0.03%/0.04%/0.18% split at closePath). |
| Tuffy-Regular, Tuffy-Italic | GSUB.script_list, GSUB.feature_list, GSUB.lookup_list | provenance | v1.272's GSUB was regenerated from glyph names (11 lookups: aalt, ccmp, dlig, frac with slash, hlig, liga HUN only, locl CAT/MOL/ROM, ordn, sups); the source and FontForge's 001.271 export carry 4 (liga, liga HUN, locl dflt/MOL/ROM, frac with fraction). At default features v1.272 loses the f+accented-i ligatures, U+2044 fractions and default-language Scedilla->Scommaaccent. Only a wholesale replacement of the four source lookups by those eleven (two of them chaining) would reproduce it. |

## Proposed .sfd edits

- **Bump the version to 1.272** (Tuffy-Regular, Tuffy-Italic) `setfield Version 1.272` -- verified: True; value from: release name ID 5 'Version 1.272; ttfautohint (v1.6)', head.fontRevision 1.272 (google/fonts b5efa9c32e8f). Optional: not a gate row.; the source stated: Version: 001.271
- **Replace the corrupt OS/2 script and strikeout metrics** (Tuffy-Regular) `setfield OS2SubXSize 1331; OS2SubYSize 1228; OS2SubXOff 0; OS2SubYOff 153; OS2SupXSize 1331; OS2SupYSize 1228; OS2SupXOff 0; OS2SupYOff 716; OS2StrikeYSize 50; OS2StrikeYPos 300` -- verified: True; value from: release OS/2 (google/fonts b5efa9c32e8f ofl/tuffy/Tuffy-Regular.ttf); the source stated: OS2SubXSize: 0, OS2SubYSize: 2, OS2SubXOff: -16560, OS2SubYOff: 0, OS2SupXSize: -25944, OS2SupYSize: -27176, OS2SupXOff: -16376, OS2SupYOff: 1, OS2StrikeYSize: 12312, OS2StrikeYPos: -16224
- **Replace the corrupt OS/2 script and strikeout metrics** (Tuffy-Italic) `setfield OS2SubXSize 1331; OS2SubYSize 1228; OS2SubXOff -32; OS2SubYOff 153; OS2SupXSize 1331; OS2SupYSize 1228; OS2SupXOff 150; OS2SupYOff 716; OS2StrikeYSize 50; OS2StrikeYPos 300` -- verified: True; value from: release OS/2 (google/fonts b5efa9c32e8f ofl/tuffy/Tuffy-Italic.ttf); the source stated: same ten corrupt values as Regular (OS2SubXOff: -16560, OS2SupXOff: -16376, ...)
- **FSType 8** (Tuffy-Regular, Tuffy-Italic) `setfield FSType 8` -- verified: True; value from: release OS/2.fsType 8. Caution: Google Fonts expects fsType 0; reproducing 8 reproduces a check failure the release already has.; the source stated: FSType: 0
- **Encode .null and nonmarkingreturn at U+0000 and U+000D** (Tuffy-Regular, Tuffy-Italic) `setencoding .null 0 0; nonmarkingreturn 13 13` -- verified: True; value from: release cmap U+0000 -> uni0000 (advance 0), U+000D -> uni000D (advance 682); the source stated: StartChar: .null / Encoding: 65536 -1 194; StartChar: nonmarkingreturn / Encoding: 65537 -1 195 (slots 0 and 13 unused)
- **Reproduce the released composite placement** (Tuffy-Regular) `setrefer Agrave 1 0 0; Aacute 1 0 0; Amacron 1 0 0; Iacute 1 0 0; eacute 1 0 0; uacute 1 0 0` -- verified: True; value from: release glyf components (A/I/e/u at 0,0); the source stated: Refer offsets A -8 (Agrave, Aacute, Amacron), I 10 (Iacute), e 10 (eacute), u 42 (uacute)
- **Reproduce the released iota-subscript layout** (Tuffy-Regular) `setrefer + setwidth alphaiotasub 1 0 0, 2 801 0, width 2013; Alphaiotasub 1 0 0, 2 801 0, width 2103; etaiotasub 1 0 0, 2 801 0, width 1865; Etaiotasub 1 0 0, 2 801 0, width 1999; omegaiotasub 1 0 0, 2 801 0, width 2009; Omegaiotasub 1 0 0, 2 801 0, width 2159` -- verified: True; value from: release glyf: uni1FB3 = uni1FBE (0,0) + alpha (801,0), advance 2013, etc.; the source stated: e.g. alphaiotasub Width 1212, Refer iotasubscript -121 0, Refer alpha 0 0; iota offsets -121/0/-467/-54/-51/17, letters at 0, widths 1212/1302/1064/1198/1208/1358
- **Make U+032E a zero-width mark** (Tuffy-Regular, Tuffy-Italic) `translateglyph + setwidth translateglyph brevesubnosp -1302 0; setwidth brevesubnosp 0; Regular only: setrefer uni1E2A 1 1252 0; setrefer uni1E2B 1 1178 0` -- verified: True; value from: release uni032E advance 0, bbox -948..-342 (= source -1302), GDEF mark; release uni1E2A/uni1E2B reference uni032E at 1252/1178; the source stated: brevesubnosp Width: 1302, outline x 354..960; uni1E2A Refer brevesubnosp -50 0; uni1E2B Refer brevesubnosp -124 0
- **Normalize gate-implicated glyphs to the released representation** (Tuffy-Regular) `importoutlines U+0162 U+0163` -- verified: True; value from: release glyf uni0162/uni0163 (1 contour each); the source stated: Tcommaaccent/tcommaaccent: 2 overlapping contours
- **Normalize gate-implicated glyphs to the released representation** (Tuffy-Italic) `importoutlines U+0162 U+0163 U+E257 U+03A9 U+1F6B U+004A U+00B7 U+0134 U+2076 U+2086 U+20B7` -- verified: True; value from: release glyf for the listed codepoints; the source stated: the source outlines (overlapping contours; fewer points, off-curve extrema)
- **OS2XHeight 500 / OS2CapHeight 700** (Tuffy-Regular, Tuffy-Italic) `addfield OS2XHeight 500; OS2CapHeight 700` -- verified: True; value from: release OS/2 sxHeight 500, sCapHeight 700. Needed ONLY once --fontforge-os2-defaults fills heights (babelfont ca43adc); with the pinned binary these rows do not exist.; the source stated: no OS2XHeight / OS2CapHeight lines

## Proposed converter changes

- babelfont: opt-in fidelity filter (e.g. --fontforge-notdef) that, when an .sfd has no .notdef, adds the glyph FontForge's TTF exporter synthesises (tottf.c dumpmissingglyph, identical 2012-06-28 and master): stem = strtod(StdVW), else strtod(StdHW) (a PostScript array such as '[70]' parses to 0), else (ascent+descent)/30 integer; ymax = min(2*(a+d)/3, ascent); xmax = 6*stem + (a+d)/10; contours (stem,0)-(stem,ymax)-(xmax,ymax)-(xmax,0) and (2*stem,stem)-(xmax-stem,stem)-(xmax-stem,ymax-stem)-(2*stem,ymax-stem); advance xmax+2*stem, lsb stem. Implementation note: babelfont resolves 'Refer: <n>' by file position, not by the Encoding gid field FontForge uses, so a synthesised glyph must be appended (or references resolved by gid); an emulation that inserted it first re-targeted references and fontc overflowed its stack.

  Evidence: Tuffy: stem 68, advance 748 = the 001.271 FontForge export and v1.272 exactly; fontc otherwise synthesises 1024/102. Emulated by appending the glyph to a copy of the .sfd: the .notdef member of hmtx.7 closes, built glyph equals the release point-for-point (runs/r3-notdef, runs/i3-notdef; probes/apply_edits.py ffnotdef).
- NOT babelfont -- sfd-batch5/tools/table_gate.py: _abs_contour_area must split contours at closePath/endPath, not at moveTo. fontTools draws a TrueType contour of only off-curve points as qCurveTo(..., None) + closePath with no moveTo, so the current code folds it into the previous contour's AreaPen and corrupts the per-contour |area| sum used by _same_geometry.

  Evidence: Closes 10 Regular and 3 Italic cmap rows, opens none (runs/r7-final/gate-closepath.txt, runs/i6-final/gate-closepath.txt: 13->3, 6->3; probes/table_gate_closepath.py replaces only that function). Allerta/AllertaStencil negative control: 182 glyphs, 0 verdicts change (runs/geom_control.txt). Should be re-run across the batch by the gate's owner.

## Unresolved

- FINDINGS.md was not written: the Write tool refused report files for subagents ('Subagents should return findings as text'). I did not work around it; the content is in this result. Probes, edit lists and run outputs are on disk under /home/fsanches/compartilhado/sfd-reland/investigations/tuffy/.
- Decision (Felipe): reproduce v1.272 (commit its defects: 43 Greek iota-subscript glyphs drawn beside, not under, the letter; fsType 8, which Google Fonts expects to be 0; and 3 GSUB rows per style that stay open) or treat Regular/Italic as provenance and land 001.271, which our build reproduces at 3 rows against the binary google/fonts shipped 2015-03..2017-10.
- GSUB.script_list/feature_list/lookup_list (Regular, Italic): provenance. Reproducing them means replacing the source's 4 lookups with v1.272's 11 (two of them chaining). That is not a minimal edit and was not tried.
- The .notdef converter change is emulated only (a glyph added to a copy of the .sfd). It still has to be implemented in babelfont.
- The table_gate.py area fix must be applied by the gate's owner and re-run across the batch. It could also close rows in other families.
- If the babelfont heights fill (ca43adc) becomes the pinned recipe, Regular/Italic need addfield OS2XHeight 500 / OS2CapHeight 700.
- sfd-batch6/B6-RESIDUALS-2026-09-22.md line 65 ('tuffy declare zero OS2Sub/Sup/Strike lines') holds only for Bold/BoldItalic. I was not allowed to edit it.
- Seen once: fontc (gftools-builder3 e851b8b) overflowed its stack on a source whose component references had been re-targeted into cycles. It should report an error. Possible upstream issue, not reduced to a minimal repro.
- Only if 001.271 is chosen: residual rows against the FontForge export are the GSUB liga lookup order (structural, 0/336 shaping differences) and head.font_direction_hint (FontForge wrote 0, we write 2).

## Rerun

    cd /home/fsanches/compartilhado/sfd-reland && for s in Tuffy-Regular Tuffy-Italic Tuffy-Bold Tuffy-BoldItalic; do TAG=tuffy OUT=investigations/tuffy/runs/r0-baseline bash tools/baseline.sh $s; done
    cd /home/fsanches/compartilhado/sfd-reland/investigations/tuffy && bash probes/run_stage.sh Tuffy-Regular r7-final --import "U+0162 U+0163" edits/both-0-version.tsv edits/regular-1-os2.tsv edits/both-2-controls.tsv edits/both-3-ffnotdef.tsv edits/regular-4-composites.tsv edits/both-5-brevesub.tsv edits/regular-5b-brevesub-users.tsv
    cd /home/fsanches/compartilhado/sfd-reland/investigations/tuffy && bash probes/run_stage.sh Tuffy-Italic i6-final --import "U+0162 U+0163 U+E257 U+03A9 U+1F6B U+004A U+00B7 U+0134 U+2076 U+2086 U+20B7" edits/both-0-version.tsv edits/italic-1-os2.tsv edits/both-2-controls.tsv edits/both-3-ffnotdef.tsv edits/both-5-brevesub.tsv
    /home/fsanches/compartilhado/gftools/venv/bin/python3 probes/table_gate_closepath.py runs/r7-final/d3.json --fonts /home/fsanches/compartilhado/google/fonts/ofl/tuffy/Tuffy-Regular.ttf runs/r7-final/built-Tuffy-Regular.ttf
    /home/fsanches/compartilhado/gftools/venv/bin/python3 probes/table_gate_closepath.py runs/i6-final/d3.json --fonts /home/fsanches/compartilhado/google/fonts/ofl/tuffy/Tuffy-Italic.ttf runs/i6-final/built-Tuffy-Italic.ttf
    BF=/home/fsanches/compartilhado/babelfont-rs-worktrees/gf-sfd-conversion/target-heights/release/babelfont bash probes/run_stage.sh Tuffy-Regular r9-heightsbin-fields --import "U+0162 U+0163" <same edits as r7-final> edits/both-9-heights.tsv   (and i8/i9 for Italic)
    bash probes/gate_vs_ff_export.sh Tuffy-Regular <baseline build .ttf> runs/vs-ff-export-1.271   (same for Italic)
    Stages r1..r6 / i1..i5: run_stage.sh with a prefix of the edit list; each run dir holds edits.log, source.diff, rows.before, rows.after, <Style>.gate.txt

## Addendum 2026-10-02: landed as plans/tuffy.json

The edits above are now `plans/tuffy.json` (tools/sfd_edit.py ops), plus what the functional
gate showed they lacked. Measured in logs/reland-2026-10-02-sfdedit/tuffy.log (babelfont
integration-names eae493be, unpublished): Regular and Italic go from 68 / 27 table-gate rows
(logs/reland-2026-10-02-final) to 0 / 0; cmap, shaping (1,270,891 runs, 0 differ), line spacing
and GDEF pass. Left: the synthesized .notdef (advance 748 vs 1024) and the localized name ID 17
in 8 languages, both converter-side.

Corrections to the text above:

- **sfd-batch5/tools/drift/import_outlines.py writes into the Back layer** when a glyph has
  one: it replaces the block's first `SplineSet`, which is the Back layer's. Tuffy's glyphs
  carry Back layers, so the r7-final / i6-final imports (and the verifier's) changed nothing
  that is built. sfd_edit's `importoutlines` writes the Fore layer. Any other plan or
  reconstruction that used import_outlines.py on glyphs with a Back layer should be re-checked.
- The release redrew far more than the 10 glyphs listed: the functional gate's geometry test
  (investigations/tuffy/probes/geometry_list.py) failed 330 Regular and 306 Italic glyphs
  before the import commit. 191 Regular (incl. Omega and tilde, which only fail inside the
  Greek composites) and 314 Italic simple glyphs are now copied from the release; Regular's 141
  failing composites then pass with their components.
- The localized style names are name ID 17 in the release (8 languages, no Spanish), not ID 2.
- The 19 combining marks need GlyphClass 4: the release's GDEF classes only them.
- 4 more composites (uni221B, uni221C, etaiotasubgrave, etaiotasubacute) take the verifier's
  placement; Alphaiotasub's first reference was already at 0 0.
