# puritan -- adversarial verification

**Model**: Claude Opus 5.5. Written from the verifier's structured result.

Reproduced: True

I extracted a fresh ofl/puritan tree from googlefontdirectory-hg 52f780bc9d19 into my scratch (inv-puritan-verify/mono) and ran their ff_scale_em.py (sha256 9248fa24) on the unmodified sources. That produced edited/intul and edited/exact. Both are byte-identical to their files. The intul sha256 prefixes are Regular b312261f, Italic fbfa0e89, Bold 16a0064d, BoldItalic 1fb24d7b.

I ran baseline.sh one style at a time with TAG=puritan-verify and OUT=scratch/runs/<v>. After removing the flags lines, every gate output is byte-identical to theirs:
- unmodified: 19/19/20/20 blocking. The BLOCKING lines match gf-source-modernization/baseline/*.gate.txt exactly.
- intul: 2/4/3/3. Regular has sx_height and s_cap_height. Italic adds us_win_ascent [880,881] and hhea.ascender [880,881]. Bold and BoldItalic add us_weight_class [700,400].
- exact: 4/6/5/5. It adds post.underline_position [-146,-100] and underline_thickness [20,50].
- italic-abs880: Italic goes to 2 (the heights only).

I also tested an alternative the investigator did not try: OS2WinAscent -1 and HheadAscent -1, keeping offset mode. It also closes Italic to 2.

No edit opened a BLOCKING row. The only new gate lines are RELEASE-STALE hmtx lsb rows: 12/33/16/28, plus the GDEF row already present.

Independent checks, written from scratch and using only the release and the built TTFs:
1. cmp_glyf.py decomposes both fonts and compares each canonicalised contour exactly. The built outlines match the release in 237/237 glyphs in all 4 styles, once degenerate controls are normalised. Advances match 237/237.
2. Without that normalisation, point structure differs in 1/5/2/5 glyphs (Regular B; Italic K f j thorn fi; Bold at braceright; BoldItalic two at f braceright approxequal). FontForge wrote an off-curve point on its own on-curve point, or wrote an explicit midpoint, and our pipeline drops or implies it. The geometry is identical and the gate does not see it. Their "point-for-point 237/237" is therefore true of their SFD-level emulation (verify_scaled_points reruns 237/237), not of the built font.
3. Width truncation, recomputed from the .sfd Width lines: int(f32(w*1.024)) matches 237/237 in all 4 styles, and rint only 107/97/113/113. This confirms their claim.
4. The heights oracle on my fresh intul sources gives 507/655 in 4/4, and 495/640 on the unmodified sources, which equals the src/*.otf.
5. Byte comparison: release Regular equals the monorepo .ttf. Italic, Bold and BoldItalic differ only in head bytes 8-11 (checkSumAdjustment) and OS/2 bytes 8-9 (fsType 1->0).
6. FFTM FFTimeStamp is 2010-04-29 03:43:27 in all four styles, equal to LibFF_ModTime 1272512607 in their ff20100501.tar.bz2 (sha256 ee4928b0..., which I rechecked).
7. I read PyFF_Font_set_em in the FontForge 20100501 sources (python.c:11527): `ds = newem*descent/oldem` is int arithmetic. SFScaleToEm rint-scales the pfminfo fields and multiplies upos/uwidth unrounded. FVTrans truncates widths through SCSynchronizeWidth and calls SCRound2Int on the active layer. `font.round()` in python.c:14708 acts on the selection only. `real` is float by default (configure.in:856).

## Verdict

VERIFY (puritan) -- **Model**: Claude Opus 5.5

VERIFY.md was NOT written. This subagent's instructions forbid writing report .md files, so the content is here instead.

VERDICT: The investigation holds up. The Puritan release is the monorepo sources with FontForge 20100501's in-memory `f.em = 1024` applied, not provenance. The proposed scaleem edit reproduces it: gate 19/19/20/20 -> 2/4/3/3, with no row opened. Independently of their tools, the built fonts match the release in outline geometry for 237/237 glyphs x4 and in advances for 237/237 x4. Widths truncate in 237/237 x4, while rint matches only 107/97/113/113. The Python-setter split 820/204 is confirmed in python.c:11527, and runs/gui-rint (819/205) fails.

Four corrections:
(1) The binaries were built at e6ab8ab47 by the original generate.py (blob 9d1f2a7b: f.em=1024, f.round(), no is_quadratic). The 52f780bc script is a later rewrite. Three .sfd were changed afterwards by e15966610 (FSType 1->0), which google/fonts 8ccda7bf7 mirrored.
(2) The Italic 880 mechanism is not encoding order. Every composite's header, in all 4 styles (3/3/8/8), is its unscaled components plus a scaled offset. Proof: Regular Scaron's xMin/xMax 41/450 equal the unscaled S (enc 83, before Scaron); yacute's header equals the unscaled y. Only Italic is affected, because Scaron is uniquely tallest there.
(3) The claim "point-for-point" holds for their SFD emulation only. The built fonts differ in point structure in 1/5/2/5 glyphs (degenerate controls); geometry is identical.
(4) The heights oracle is valid for the 20100501 vintage here, because the flats branch applies (modes 507/655). The ca43adc converter commit is not in the pinned binary.

Edit verdicts:
- scaleem: keep the transformation, revise the body (cite the e6ab8ab47 script and the tool sha; mention the stale em-1000 TT instructions; keep the underline note). Add a scope guard before making it a general op.
- Italic OS2WinAscent/HheadAscent 880 plus the two offset-flag commits: keep as a verified fallback. The offset -1 form is also verified and uses 2 lines instead of 4.
- Gate arbitration versus fallback is Felipe's decision. The current table_gate.py (_bbox_declared) keeps those rows BLOCKING.
- Converter proposal (parse UnderlinePosition/Width as f64 and apply (short)(upos-uwidth/2)): valid, because babelfont fontforge.rs:92 parse::<i32> drops reals silently. Low priority.

PINS:
- babelfont 0.2.1: binary built 2026-09-23 20:27:57 (f725e6a); the worktree HEAD is now ca43adc, not built.
- gftools-builder e851b8b (fontc 1.0.0); diffenator3 1.1.4
- table_gate.py: sfd-batch5 f5cb410, sha256 391e296d3f6e0768
- baseline.sh sha256 c76a392f07676a4a; ff_heights_oracle.py sha256 c7647148524e0544
- google/fonts b5efa9c32e8f; googlefontdirectory-hg 52f780bc9d19 (binaries from e6ab8ab47)
- FontForge 20100501 tarball sha256 ee4928b0df74...

RERUN (S=/tmp/claude-1000/-home-fsanches-compartilhado-GoogleFonts/f55394dc-b840-4055-b5b4-e2463e4b4dd8/scratchpad/inv-puritan-verify, A=/home/fsanches/compartilhado/upstream_repos/repo_archive/googlefonts/googlefontdirectory-hg.git, PY=/home/fsanches/compartilhado/gftools/venv/bin/python3, R=/home/fsanches/compartilhado/google/fonts/ofl/puritan):
1. git -C $A archive 52f780bc9d197280a9f430574e179a5f233c56b6 ofl/puritan | tar -x -C $S/mono --strip-components=2
2. for s in Regular Italic Bold BoldItalic; do $PY $S/tools/ff_scale_em.py $S/mono/src/Puritan-$s.sfd $S/edited/intul/Puritan-$s.sfd --int-underline; done
3. cd /home/fsanches/compartilhado/gf-source-modernization; for s in ...; do TAG=puritan-verify OUT=$S/runs/intul SRC_OVERRIDE=$S/edited/intul/Puritan-$s.sfd bash tools/baseline.sh Puritan-$s; done  (also runs/unmodified, runs/exact, runs/italic-abs880, runs/italic-off-1)
4. $PY $S/tools/cmp_glyf.py $R/Puritan-$s.ttf $S/built/intul/Puritan-$s.ttf [--degen]   (built fonts copied from scratchpad/baseline/Puritan-$s-puritan-verify/fonts/ttf)
5. $PY $S/tools/bbox_probe.py $R/Puritan-*.ttf
6. git -C $A show e6ab8ab47:puritan/src/generate.py; git -C $A show e15966610 -- puritan/

All my probes are scratch-only (volatile). They must be committed next to these numbers before anyone cites them.

## Per edit

- [revise] Scale the em to 1024 as src/generate.py did -- Keep the transformation exactly as proposed. It is reproduced and gate-verified: 19/19/20/20 -> 2/4/3/3 with no row opened, built geometry 237/237 x4 and advances 237/237 x4. It discards no designer-stated value: every stated metric is rescaled by FontForge's own rule, offset flags stay offsets, and HheadDescent -18/-1/-8 is unchanged by rint. No fidelity route exists, because the exporter writes UPM = Ascent+Descent; the 1024 comes from the build script. value_derived_from is honest: no number is taken from the release, which is used only through FFTM to identify the FontForge version.  Revise the commit body only: (1) The binaries were built at e6ab8ab47 (2010-11-26 14:22) by the ORIGINAL generate.py (blob 9d1f2a7b: f.em = 1024 then f.round(), no is_quadratic, file names 'Puritan.sfd' etc.). The 52f780bc script is a later rewrite (15d6ae4fd on 11-29, acd4730e6 on 11-30). Cite 'generate.py as committed with the binaries in e6ab8ab47'. (2) Name the implementing tool and its sha (ff_scale_em.py 9248fa24) and the FontForge 20100501 identification. (3) Keep the sentence saying -136/20 is a rounding of FontForge's -136.192/20.48 that exports the same post bytes. This choice does work around a real converter bug (i32 parse silently drops reals), and that bug should be filed regardless. (4) Say that the .sfd still carries em-1000 TrueType instructions: TtInstrs in 229/229/224/224 glyphs, plus the cvt, prep and fpgm tables. The release regenerated these with autoInstr, and the converter ignores them.  Before the scaleem op goes into source_corrections.py, it needs a guard. It must refuse sources with KP/KernClass2/AnchorPoint/HStem/VStem/BeginPrivate/BASE/math data: FontForge scales these (fvt_scalekernclasses, fvt_scalepstpos, SFScalePrivate) and the port silently does not. None is present in Puritan (checked).
- [keep] OS2WinAscent 880 -- This is the fallback only, and it is verified: Italic goes 4 -> 2 with nothing opened. The source states OS2WinAscent 0 with OS2WinAOffset 1 (bbox + 0). 880 exists only in the release, and the body says so plainly and says it clips Scaron by 1 unit. The facts in the body are right: the Scaron glyf header yMax is 864 while the outline reaches 881; caron is all on-curve lines (top 727+154=881), so no curve-extrema fidelity explanation applies; Aring (simple) is 880.  An equally verified, smaller alternative is OS2WinAscent -1 in offset mode, with no companion flag commit. Absolute plus flag follows the existing precedent, so either is acceptable.  Felipe should decide between this and the gate rule.
- [keep] OS2WinAOffset 0 -- Companion of OS2WinAscent 880. The source states 1; the body 'Value above is absolute.' matches precedent. Not needed if the offset -1 form or gate arbitration is chosen.
- [keep] HheadAscent 880 -- Fallback only, verified together with OS2WinAscent 880 (runs/italic-abs880 reproduced byte-identically). The source states HheadAscent 0 with HheadAOffset 1. The value is release-only and the body is accurate. HheadAscent -1 in offset mode also closes the row (verified).
- [keep] HheadAOffset 0 -- Companion of HheadAscent 880. The source states 1. Drop it if the offset -1 form or gate arbitration is chosen.

## Objections

- Italic OS/2.us_win_ascent [880,881] and hhea.ascender [880,881] (gate-arbitration): the fact is right but the stated mechanism is wrong. The findings say FontForge 'scaled Scaron (slot 0xA6) before caron (slot >255)'. The release contradicts an ordering effect. The Regular Scaron header xMin/xMax 41/450 is the UNSCALED S (41/450), although S (enc 83) comes before Scaron (enc 166). The yacute header (22,-196,458) is the unscaled y (enc 121 < 253). Stale composite headers exist in all four styles (3/3/8/8), and their own stale_composite_bbox.py predicts 22/22 of them. That script models EVERY component as unscaled, regardless of order. The correct statement is that every composite's cached reference geometry stayed unscaled with a scaled offset: SCTransLayer only translates a selected reference (fontviewbase.c, 20100501). Only Italic is affected, because Scaron is uniquely tallest there. In Regular, .notdef (simple) also reaches 881; in Bold and BoldItalic, Icircumflex/Ecircumflex reach 896. Also, the proposed gate arbitration does not exist yet. _bbox_declared deliberately says nothing when head bboxes differ (table_gate.py:555-584), so these rows stay BLOCKING until Felipe approves a gate change or the fallback edit. A gate rule should compare resolved extremes by one method on both sides; FontForge's simple-glyph headers use curve extrema, not control points.
- Provenance narrative (it affects no row class, but the text should be corrected): 'exactly the four .sfd at 52f780bc run through that tree's generate.py' is imprecise. The binaries were committed at e6ab8ab47 with the original generate.py (no is_quadratic). Three .sfd were changed afterwards by e15966610 (2011-01-26, 'Removing OpenType DRM bits': FSType 1->0 in Italic/Bold/BoldItalic); the monorepo TTFs still carry fsType 1 and google/fonts 8ccda7bf7 mirrored the fix, so no row results. The Regular .sfd blob 698e56ac is unchanged since e6ab8ab47. The FFTM sourceModified values equal the .sfd ModificationTime (14:05:32/33/34/34), which corroborates that the outline state is unchanged.
- OS/2.sx_height / s_cap_height (converter-fidelity): I agree, and I add evidence they omitted. The oracle ports FontForge MASTER. Its one semantic difference from 20100501 (splinefont.c SFStandardHeight, no-flat branch: 'tot += curves[i].cnt' vs '++tot') is not exercised here. All 4 scaled styles take the FLATS branch, with modes 507 (x-height) and 655 (cap height). So the oracle is valid for this vintage. Caveat: the converter commit ca43adc now sits in the babelfont worktree, but target/release/babelfont (built 20:27:57) predates it (committed 20:56:25). Closure is proven by the oracle only, not by a build.
- hmtx.N bearings rows (source-edit-from-source): I agree they close. But the residual RELEASE-STALE lsb rows are 12/33/16/28 hmtx rows (13/34/17/29 counts the GDEF row too). The explanation 'FontForge's lsb follows curve extrema' matches only 52 of 72 simple-glyph rows (floor/round of fontTools BoundsPen xMin). For example, Italic e has lsb 32 against a curve xMin of 31.35, and Italic questiondown has 11 against 10.0. These rows are non-blocking and gate-arbitrated already, but the stated cause is partial.

## Missed

- The generate.py history: the binaries were built by the e6ab8ab47 script, and the 52f780bc script is a 2010-11-29/30 rewrite. The commit body and value_derived_from should cite the original.
- The post-build .sfd edit e15966610 (FSType 1->0, three styles). It is neutralised by google/fonts 8ccda7bf7, but it means the 52f780bc .sfd is not byte-for-byte the build state.
- Stale composite headers in Bold and BoldItalic (8 each: edieresis, igrave, icircumflex, odieresis, udieresis, Scaron, scaron, yacute). They ran the predictor only on Regular and Italic.
- The built font is point-for-point only modulo degenerate controls: 1/5/2/5 glyphs differ in point structure while their geometry is identical. The gate is unaffected.
- The scaled .sfd keeps stale em-1000 TtInstrs, cvt, prep and fpgm. The converter ignores them, and the release regenerated them with autoInstr.
- The new scaleem op has no guard against data FontForge would scale but the port ignores (kerning, anchors, hints, private dict, BASE, math). This is safe for Puritan only.
- The babelfont worktree HEAD moved to ca43adc (heights) after the pinned binary was built. The heights closure is unbuilt and unverified end-to-end.
- The offset-mode alternative for Italic (OS2WinAscent -1 / HheadAscent -1, 2 lines instead of 4) also closes both rows (verified).
- Pairing is correct: each .sfd FontName equals the release post_script_name and the METADATA.pb filename. All 4 styles are covered, and all 78 given rows are classified. No BLOCKING row is opened by any proposed edit.
- Reproducibility: their tools, their edited sources and my probes (inv-puritan-verify/tools: cmp_glyf.py 63af2d1a, bbox_probe.py aa5c206d, probe_release.py fd67592a, show_glyph.py a4034f6c) exist only in untracked or scratch locations. Under the global rule they must be committed next to the numbers before the edit lands.
