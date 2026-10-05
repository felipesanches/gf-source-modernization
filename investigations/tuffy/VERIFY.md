# tuffy -- adversarial verification of the investigation's findings

**Model**: Claude Opus 5.5 -- 2026-09-23

Pinned: babelfont gf-sfd-conversion `f725e6a` (target/release, baseline.sh default) and
`ca43adc` (target-heights, BUILT_FROM, what land.py uses); gftools-builder3 `e851b8b`
(fontc 1.0.0); diffenator3 1.1.4; table gate `sfd-batch5/tools/table_gate.py` at
`f5cb410` until 21:17:49 and `cd4f827` after (see 1); release google/fonts `b5efa9c32e8f`;
sources googlefontdirectory-hg `52f780bc` `ofl/tuffy/src/Tuffy-<Style>-TTF.sfd`.
Probes and the rerun script: `verify/` (README there). Nothing committed.

## Verdict

Reproduced exactly. Every row count they report holds, and my independently written edits
produce the same sources as theirs, line for line, except the Flags line of the synthesized
.notdef. The provenance story is sound: Bold and BoldItalic are FontForge exports of these
.sfd files. Regular and Italic are v1.272, made in 2017 from FontForge's 001.271 export.
I have three objections:

1. **The composite-placement edits are incomplete.** v1.272 moved the first component of 4
   more composites to (0,0): uni221B, uni221C, etaiotasubgrave and etaiotasubacute. The gate
   cannot see these moves because advance, bbox and area are unchanged. They still render
   46.5%, 18.7%, 12.1% and 12.1% of their pixels differently. Adding 4 `setrefer` edits
   brings all four below 1%, and the gate still shows 3 rows.
2. **The T/t-comma rows (both styles) and aogonekalt (Italic) are overlap-only.** Our
   unmodified build renders them within 0.02-0.18% of the release. The gate adds up the
   |area| of each contour, so it counts the overlap twice. These rows are gate-arbitration,
   not source edits.
3. **Some commit bodies need rewording.** Details in 2.

## 1. Reproduction (verify/rerun.sh)

| style | baseline | all proposed edits | + gate cd4f827 | + 4 composites | landing bin ca43adc: without / with height fields |
|---|---|---|---|---|---|
| Regular | 74 | 13 (= their r7-final rows.after) | 3 (GSUB x3) | 3 | 5 / 3 |
| Italic | 27 | 6 (= their i6-final rows.after) | 3 (GSUB x3) | -- | 5 / 3 |
| Bold, BoldItalic | 1 each (us_weight_class) | -- | 1 | -- | 1 |

- I built the edited sources with `verify/verify_apply.py`, written independently of their
  `apply_edits.py`, starting from `git show 52f780bc:...`. `diff` against their
  `runs/{r7-final,i6-final}/source.diff` finds one difference: the synthesized .notdef's
  `Flags:` line.
- **The gate changed during this verification.** sfd-batch5 `cd4f827` (21:18,
  "table_gate: end a contour at closePath, not at the next moveTo") adopts their proposed
  area fix. Under it the unmodified baselines drop to Regular 64 and Italic 24, so
  `baseline.tsv` and `baseline/Tuffy-{Regular,Italic}.gate.txt` are stale for tuffy.
- I also reimplemented the split independently (`verify/gate_contour_split.py`). On my
  builds it gives 13->3 and 6->3. Their four gate-closepath.txt files are byte-identical.
  That is genuine: my Regular and Italic outputs are identical too, because the rename lists
  and row texts coincide.

## 2. Per-edit verdicts

| commit | source states | verdict |
|---|---|---|
| Bump the version to 1.272 | `Version: 001.271` | keep. Optional (not a gate row) and only if v1.272 is the target. |
| Replace the corrupt OS/2 script and strikeout metrics (R, I) | the ten garbage values, verbatim in FontForge's own 001.271 export and in the 2011 .otf | keep, revise body |
| FSType 8 | `FSType: 0` | keep only if v1.272 is the target. It discards a stated value to reproduce a GF check failure. |
| Encode .null and nonmarkingreturn at U+0000 and U+000D | `65536 -1 194` / `65537 -1 195` | keep. Slots 0 and 13 are free, and file order = gid order (babelfont resolves `Refer` by file position). |
| Reproduce the released composite placement | A -8, I 10, e 10, u 42 | revise: add uni221B (threesuperior 172 7 -> 0 0) and uni221C (foursuperior 68 0 -> 0 0) |
| Reproduce the released iota-subscript layout | iota -121/0/-467/-54/-51/17 | revise: add etaiotasubgrave (-464 -> 0) and etaiotasubacute (-468 -> 0). Drop `setrefer Alphaiotasub 1 0 0`, a no-op (already 0 0). |
| Make U+032E a zero-width mark | Width 1302, outline 354..960 | keep. Italic has no `Refer:` lines at all, so there are no users to adjust. |
| Normalize ... (Regular U+0162 U+0163) | 2 overlapping contours | revise: gate-arbitration (see 3). Import only as a fallback. |
| Normalize ... (Italic, 11 codepoints) | source outlines | revise: split it. U+0162, U+0163 and U+E257 are overlap-only (gate-arbitration). Keep the 8 refits. |
| OS2XHeight 500 / OS2CapHeight 700 | absent | keep. Needed with ca43adc (5->3 verified). The keywords are real FontForge SFD (`sfd.cpp`, fontforge master `606b33dc`). |

Body revisions:

- **OS/2 metrics.** OTS 9.2.0 accepts the 001.271 export: exit 0, "File sanitized
  successfully". It only warns about the two negative superscript sizes, and zeroes them.
  The release values are the 2017 tool's defaults:
  - 1331, 1228, 153 and 716 are 0.65, 0.6, 0.075 and 0.35 em, truncated;
  - 300 is 0.6 x the default x-height of 500;
  - the Italic x offsets are tan(11.85 deg) x 153 = 32.1 and tan(11.85 deg) x 716 = 150.2.
    11.85 is the release's italicAngle; the source states `ItalicAngle: -12`.

  Say "exist only in the release, as tool defaults".
- **OS2XHeight / OS2CapHeight.** Say plainly that 500/700 are not the design's heights.
  FontForge's rule and FontForge's own 2011 .otf export give 1069/1450.
- **Composite placement.** "first component to the origin", not "base component".

## 3. Classifications

- **Agree:**
  - Bold/BoldItalic us_weight_class: converter-fidelity, in progress. The sha1 matches,
    and FFTM sourceModified equals the .sfd ModificationTime to the second for all four
    styles (1314725042 / 463 / 717 / 601).
  - .notdef: converter-fidelity. tottf.c `dumpmissingglyph` has the same logic in 2012 and
    in master. The 001.271 export and both releases carry exactly those 8 points. Our
    emulation has the same points in the same cyclic order, but starts each contour at a
    different point, so "point-for-point" is loose. The spec also omits the monospace
    branch: the advance becomes the fixed width, and the glyph is synthesized whenever
    .notdef's width differs from it.
  - GSUB: provenance. The release has 13 lookups (2 of them chaining), not 11. Our build
    against the 001.271 export gives 3 rows: GSUB x2 and head.font_direction_hint [0, 2].
- **Object: U+0162/U+0163 (R, I) and U+E257 (I).** These are gate-arbitration, not
  source-edit-from-release.
  - FreeType renders release vs our unmodified build 0.02-0.18% of pixels apart. The
    001.271 export vs ours is 0.00-0.02%.
  - `verify/gate_either_area.py` passes a glyph when the per-contour sum OR the
    filled-region area agrees. It closes exactly these 5 rows and opens none. On the
    Allerta/AllertaStencil control it leaves 71 = 71 verdicts unchanged.
  - A filled-region measure alone would instead open U+041E, U+1F48 and U+1FF8 in Italic.
- **Caveat: U+03A9/U+1F6B (Italic).** Keep, but these are threshold-marginal. The
  unmodified Italic has 105 codepoints at >= 0.5% of pixels with no cmap row of their own
  (108 minus U+032E, U+03A9 and U+1F6B), e.g. Omicron 0.84%.
  U+2126 (Ohm) has the same 0.71% refit as Omega and is not imported.
- **J family (Italic).** FontForge wrote curve-extremum xMin/lsb, which is why OTS warns
  "Glyph bbox was incorrect". So FontForge's lsb equals the release for J, Jcircumflex and
  uni20B7, but not for periodcentered, uni2076 or uni2086. This gives no fidelity route;
  the import stands.

## 4. Pairing

Everything matches families.tsv. Each style pairs `src/Tuffy-<Style>-TTF.sfd` with
`google/fonts ofl/tuffy/Tuffy-<Style>.ttf`, and their `run_stage.sh` uses the same pairing.
The non-TTF `.sfd` files (001.270, ModificationTime 1314198286) are the sources of the
2011 `.otf`s, not of the TTFs.

## 5. Missed

- **Four gate-invisible composite moves**, as in objection 1. The evidence is in
  `component_moves.py` output:
  - 1.271 vs v1.272: 66 composites differ.
  - After their edits: 15.
  - After the 4 extra edits: 11, all equivalent re-spellings (quotes, periodcentered,
    Ldot/ldot) that render within 1%.
- **v1.272 differences outside the gate that the edits do not reproduce:**
  - post.italicAngle -11.85 vs -12 (Italic);
  - render refits: U+2208 1.5% and U+10910 1.0% (Regular); U+2024 1.35%, U+10910 and
    U+2026 1.0% (Italic).
- **Their FINDINGS.md is still missing.** I left it unwritten because those are their files.
- **Choosing 001.271** would mean re-pointing families.tsv at google/fonts `90abd17b4` or
  monorepo `52f780b`. That is a pairing change for Felipe to approve.

## Rerun

    bash /home/fsanches/compartilhado/gf-source-modernization/investigations/tuffy/verify/rerun.sh
    # builds one at a time into $W (default session scratch); prints every gate summary line.
    # Last run (21:5x): base 64/24/1/1; R-full 3, I-full 3, R-full-plus4 3 (gate cd4f827);
    # ca43adc 5 -> 3 with the height fields; raster/component/gate-variant files as quoted;
    # step 8 re-gates R-full / I-full with the pre-fix gate f5cb410: 13 / 6.
