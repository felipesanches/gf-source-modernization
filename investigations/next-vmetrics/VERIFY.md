# next-vmetrics -- adversarial verification

**Model**: Claude Opus 5.5. Written from the verifier's structured result.

Reproduced: True

All reproduced on the pipeline's own pairing (families-next.tsv: googlefontdirectory-hg @52f780bc <lic>/<fam>/src/*-TTF.sfd vs google/fonts b5efa9c32e8f <shipped>). Outputs are under /home/fsanches/compartilhado/sfd-reland/investigations/next-vmetrics-verify/{probes,runs}. The brief named two locations; I used next-vmetrics-verify, as its Files section says. Scratch is under sfd-reland-scratch/vmetrics-verify/. Nothing is committed.

(1) Baseline (runs/00-baseline) matches baseline-next: 11 rows (Limelight 5, MoC-Bold 4, NYCD 2).

(2) New parser, written without reusing unifraktur/vmetrics_probe.py (probes/indep_bounds.py, runs/indep_bounds.txt). It gives the claimed values:
- MoC-Bold under the pre-2014 on-curve rule: 1064/354/1066/-354, equal to the release. The extremes are where the investigation says: Scaron on-curve 1056, curve 1058.0, control 1060; g on-curve -354, curve -354.381, control -356.
- NYCD: 959/407/959/-407, equal to the release. The extreme is a circumflex at 959.439 on-curve 959, control 962; Hcircumflex ties with Ecircumflex.
- Limelight: FontForge's rule gives 1881/631/1881/-632, #85 gives 1881/633/1881/-633, and the release has 1864/629/1864/-629. That is int() of the true extremes (1864.0 uni1E1F, -629.28 kcommaaccent). The release's own TTF outlines give the same int() values, which matters because vmetcheck.py opens the .ttf.

(3) FontForge code fetched at b69c9652 and c9ca2f32. dumpglyph, dumpcomposite, SplineSetQuickBounds, SplineCharLayerQuickBounds, SCttfApprox, sethhead, WinBB and dumpghstruct are byte-identical in both. setos2/WinBB runs after sethead (initATTables is called after sethead). Master counts control points (ee15007274e9, 2014-09-16T19:35:46Z = 1410896146, confirmed via the GitHub API).

(4) Sweep of all 149 styles with the new parser (runs/indep_sweep.txt): 328 offset-mode metrics in 82 styles. Pre-2014 rule 305, #85 298, master 295; identical to the investigation. The pre-2014 rule never misses where #85 hits. Its 23 misses are Limelight 4, Play-Bold 3 and Puritan 16. Only 4 styles differ between the pre-2014 rule and #85.

(5) Glyph boxes (runs/glyph_boxes.txt): Limelight has 21 all-point-only boxes and 0 FontForge-only. Counting composites too: MoC-Bold v1.003 has 193 FontForge-only boxes and 0 all-point-only; NYCD 295 and 0.

(6) Pairings and releases. MoC-Bold v1.003 (f3ec322aa) has the same vertical metrics, head box and outlines as v1.002 (90abd17b4). Limelight's other candidate, -OTF.sfd, is cubic and its ModificationTime is 17:24:59; FFTM sourceModified 21:31:23 matches -TTF.sfd, so the pairing is right. The designer's src/Limelight-Regular.otf carries 1881/-634 in typo, win and hhea, with win descent 634.

(7) Limelight .sfd edit: applied with sfd_edit.py (runs/limelight-vmetrics-edit.verify.diff). CLEAN on the pinned converter (runs/01) and with the filter (runs/04).

(8) I rebuilt the prototype myself from next-vmetrics/runs/babelfont-proto.diff on integration-ff-prs 17ea899 (sha256 64b4ae45..., which differs from the investigation's build because the build embeds its path).
- Results: MoC-Bold 4 -> 1 (runs/02) -> 0 with land.py's weight-class workaround (runs/03). NYCD 2 -> 0. MoC-Regular CLEAN. UnifrakturMaguntia-Book leaves 3 GPOS rows (runs/06).
- The filter's 3 tests pass and fmt is clean (runs/proto-rebuild-checks.txt). I did not re-run clippy.

(9) Implementation against model (runs/impl_vs_model.txt). I converted all 149 styles with the pinned converter and with the prototype. On 328/328 offset-mode metrics the prototype equals my on-curve model and the pinned converter equals my #85 model. 0 of the other 566 metrics move, and exactly 4 styles change.

(10) FFTM: every stamp in both tables is 2012-09-06 or earlier; 8 releases have no FFTM.

## Verdict

The investigation holds. Using my own parser, the FontForge source I fetched myself, harness runs and a rebuild of the prototype from its diff, I reproduced:
- every row cause and every harness result;
- the 305/298/295 model counts;
- the "4 styles change, none regresses" claim.

The Rust filter matches an independent model on all 328 offset-mode metrics in both tables. The Limelight .sfd edit is sound: its values equal int() of both the source's and the release's true extremes. The edit closes all 5 rows.

Weak points, none of which change a row or block landing:
1. The us_weight_class row uses a new label, 'compiler-gap'. Every earlier unit called the same row converter-fidelity.
2. vmetcorrect.py is omitted. It is the repository's tool that applies the cited rule, in the same IsOffset=0 + value shape as the proposed edit.
3. GiveYouGlory is mischaracterised. By the result's own tests it is a clean FontForge 20110222 export, yet the filter's rule misses 2 of its 4 metrics. The upstream PR should present the rule as validated on the 82 offset-mode styles of these tables, not as complete for pre-2014 FontForge.
4. The Limelight commit body leans on head.modified, which ttfautohint alone explains. The hmtx-vs-glyf fingerprint is better evidence.

Families landable after the changes, as the result says:
- limelight: the edit alone.
- nothingyoucoulddo: the babelfont filter plus the recipe change.
- mountainsofchristmas: the filter, the recipe change and land.py's existing weight-class workaround.

All three still wait on #91-#93 and the new PR being merged upstream.

## Per edit

- [keep] Set the vertical metrics the 2012 release carries -- The values reproduce independently: 1864/629/-629 = int() of the true extremes, both of the .sfd outlines and of the release's own TTF outlines (which vmetcheck.py measures). FontForge's own rule gives 1881/631/1881/-632, and no rule gives 629 from the stated offset 3 (on-curve 631, all-points 639, #85 633). The value's origin is disclosed. The absolute form (flag 0 + value) is the same shape as tools/bbox/vmetcorrect.py's set_os2_vert, so it is the natural .sfd form, and it is converter-rule independent (CLEAN in runs/01 and with the filter in runs/04). Typo descender -634 is correctly left alone. Optional wording fixes: (a) 'head.modified says 2012-08-20' is not evidence of the METRICS edit by itself, because the same hg commit added ttfautohint hinting, which re-stamps modified. The stronger evidence is the 21 all-point glyph boxes plus 9 hmtx LSBs that kept FontForge's on-curve value while glyf xMin moved to the all-point minimum (runs/limelight_hmtx_vs_glyf.txt). (b) Say 'the int() rule of tools/bbox/vmetcheck.py and vmetcorrect.py', not that the script was run: neither script's automated output matches the release, since both would also change TypoDescent.

## Per tool change

- [keep] babelfont-rs: opt-in filter --fontforge-legacy-offset-metrics (reader records sfd.offset_delta.<key>; filter re-resolves win from the on-curve head box, hhea from truncated true extremes widened to it) -- The code matches FontForge b69c9652/c9ca2f32 (dumpglyph and dumpcomposite on-curve QuickBounds with floor/ceil, sethhead truncation and widening, WinBB). The SFD reader keeps flag-128 implied points as QCurve nodes, so they count as on-curve, as FontForge's SplinePoints do. My rebuild from the diff reproduces every harness result, and on all 149 styles it equals an independent model on 328/328 metrics and moves nothing else. Tests and fmt pass. Mergeability: it is opt-in; there is precedent for filters reading sfd.* keys (fontforgeos2defaults reads sfd.width_set); no sfd.* keys leak into .glyphs output; it depends only on the open #91-#93 for its group line. Requested revisions to the doc comment/PR text, none blocking: (1) state that the pre-2014-10 sethhead quirk (hhea descender's mode taken from HheadAOffset) is not modelled. (2) Do not claim the rule is universal for pre-2014 FontForge: GiveYouGlory is a clean 20110222 export (head created == modified, 339 FontForge on-curve boxes, 0 all-point) where it misses 2 of 4 metrics (runs/indep_bounds_pr85_pairs.txt, runs/glyph_boxes_giveyouglory.txt, runs/stamps.txt). (3) 'Must run first' is design rationale only: with the flag last, MoC-Bold and NYCD give identical results (runs/07-flag-last).
- [keep] sfd-reland tools/recipe.py: insert --fontforge-legacy-offset-metrics first when the release's FFTM build stamp < 1410896146 (ee15007274e9) -- The cutoff is the verified commit time of ee15007274e9. It uses the same FFTM mechanism as --fontforge-height-glyph-count-mean. It adds the flag to all 141 FFTM-stamped styles, but only 4 change (runs/impl_vs_model.txt), and none moves away from its release. The FFTM stamp is FontForge's library_source_modtime (ttfspecial.c ttf_fftm_dump), so a stamp can only postdate the code, never predate it; the gate cannot wrongly apply the pre-2014 rule to post-2014 code. Apply only after the converter change is merged upstream and the pinned converter is rebuilt from a published revision, as the investigation says.

## Objections

- MountainsofChristmas-Bold OS/2.us_weight_class [700, 400] is labelled 'compiler-gap'. That label is not in the taxonomy the workflow journal uses. Every earlier unit classified the identical fontc single-master weightClass row as 'converter-fidelity': corben-bold, heights (NosiferCaps, UnifrakturCook-Bold), nosifer, puritan (Bold, BoldItalic), small (ComicRelief-Bold), tuffy, play (Play-Bold). Relabel it converter-fidelity. It is closed by tools/workarounds.py weight_class, which I reproduced: runs/03 has 0 blocking rows. The other 10 rows' classifications are correct: Limelight 5 x source-edit-from-release; MoC-Bold 3 and NYCD 2 x converter-fidelity.

## Missed

- googlefontdirectory-hg 927784141:tools/bbox/ also holds vmetcorrect.py, which APPLIES the same int() rule the result cites from vmetcheck.py. It sets each metric's IsOffset to 0 and writes the absolute value (set_os2_vert), exactly the shape of the proposed .sfd edit, then calls FontForge Generate. It cannot be the final writer: it would also set TypoDescent -629, its WinDescent branch writes the negative ymin, and a FontForge Generate would give created == modified and on-curve boxes. It should still be named as the repository's tool for this rule.
- Extra evidence for the Limelight post-export rewrite that the result did not use (runs/limelight_hmtx_vs_glyf.txt). All 9 RELEASE-STALE hmtx rows in the gate have the same fingerprint: hmtx lsb is FontForge's on-curve x-minimum while glyf xMin is the all-point minimum (e.g. 'one' lsb 1 vs xMin -2; 'seven' 64 vs 61). The boxes were therefore recomputed without touching hmtx, which is what a fontTools/ttx compile (recalcBBoxes) does. FontForge writes lsb and xMin from the same box, and ttfautohint keeps glyf headers. This narrows the 'tool not identified' item, though it does not prove it.
- GiveYouGlory is mischaracterised. The result says its 621 'suggests another post-export edit', but by the result's own discriminators it is a clean FontForge 20110222 export: head.created == head.modified (2011-07-08 07:31:04); FFTM sourceModified == the .sfd ModificationTime (1310121007); 339 glyph boxes are FontForge on-curve boxes and 0 are all-point (runs/stamps.txt, runs/glyph_boxes_giveyouglory.txt). Yet the pre-2014 rule gives 619/-624 against the release's 621/-625, and vmetcheck's rule gives -621 against -625, so it is not a vmetcheck edit either. Neither rule explains it; the stated offsets at export may have differed. At b69c9652, sf->modificationtime is bumped only by Font Info OK (fontinfo.c GFI_OK -> SFSetModTime), not by saving, outline edits or scripted SetOS2Value, so FFTM == ModificationTime does not prove the exported metrics equal the committed file. It is outside both tables, so no row here changes, but it lowers confidence that the filter's rule is complete.
- Minor evidence caveats. The control counts '137/143' cover simple glyphs only, and MoC-Bold's control is v1.002 (90abd17b4), not the paired v1.003 release. Counting composites, the paired releases have 193 and 295 FontForge-box glyphs and 0 all-point-only; the conclusion is unchanged. The '10 s after the save' wording is loose: FFTM sourceModified is the last Font Info OK time (sf->modificationtime), not the save time. The extreme-setting glyph names have ties: Rcommaaccent/kcommaaccent for the Limelight minimum, Hcircumflex/Ecircumflex for the NYCD maximum.
- No pairing mistakes were found. families-next.tsv has no duplicate style rows. Limelight's two candidates are resolved correctly (FFTM sourceModified = -TTF.sfd, not -OTF.sfd). NYCD's and Limelight's shipped blobs are the hg files. MoC-Bold's 2017 hotfix did not touch vertical metrics or outlines.
