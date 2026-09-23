# small -- adversarial verification

**Model**: Claude Opus 5.5 -- 2026-09-23

Pinned: babelfont gf-sfd-conversion `f725e6a` (target/release, the baseline.sh default)
and `ca43adc` (target-heights/release); gftools-builder3 `e851b8b` (fontc 1.0.0);
diffenator3 1.1.4; table gate sfd-batch5 `tools/table_gate.py` at `cd4f827` (repo HEAD
`cad44be`); release google/fonts `b5efa9c32e8f`. Sources, per families.tsv:
googlefontdirectory-hg `52f780bc` `ofl/russoone/src/RussoOne-Regular-TTF.sfd` and
`ofl/tuffy/src/Tuffy-{Regular,Italic}-TTF.sfd`; loudifier/Comic-Relief `856315f`
`sources/ComicRelief-{Regular,Bold}.sfd`. sfdLib 2.0.0.post0 (PyPI wheel, sha256
18aae8c9...) run with ufo2ft 3.7.0 / fontTools 4.61.1 (gftools venv). ufo2ft 3.4.1 read
from its v3.4.1 tag. FontForge tottf.c/sfd.c read at tags 20170731, 20190317, 20200314,
20230101.

Probes, run outputs and the rerun script are in `verify/` (see verify/README.md). The
investigation's own files were read, not modified. Nothing was committed.

## Verdict

Reproduced exactly. I made every edited copy fresh from the archive with
`tools/sfd_edit.py`, and each harness run gives the same BLOCKING and RELEASE-STALE lines
as theirs. The RussoOne edit stands. The ComicRelief classification stands, and there is
stronger evidence for it than they gave. The converter-rule spec needs revising (see 2).
No edit or simulation opens a new row.

## 1. Reproduction (verify/rerun.sh -> verify/runs/gate_summary.txt)

| run | converter | blocking rows |
|---|---|---|
| RussoOne-Regular, FSType 0 | f725e6a | 1: OS/2.sx_height [530, 500] |
| RussoOne-Regular, FSType 0 | ca43adc | 0 (CLEAN) |
| ComicRelief-Regular, no underline flag | f725e6a | 1: post.underline_position [-97, -185] |
| ComicRelief-Regular, SIM -97 | f725e6a / ca43adc | 0 / 0 |
| ComicRelief-Bold, no underline flag | f725e6a | 2: us_weight_class [700, 400], underline [-97, -185] |
| ComicRelief-Bold, SIM -97 | f725e6a / ca43adc | 1 / 1: OS/2.us_weight_class [700, 400] |

- `setfield FSType 0` changes line 18 only (`FSType: 4` -> `FSType: 0`). My copy is
  byte-identical to their edits/RussoOne-Regular-TTF.fstype0.sfd.
- The RELEASE-STALE sets match baseline/*.gate.txt (7 for RussoOne, 1 for ComicRelief).
  Every run printed its closing "N blocking table difference(s)" line.
- conv_checks.txt, for both converter builds:
  - The SIM copy's .glyphs differs from the unmodified conversion in exactly one line,
    `underlinePosition` -185 -> -97.
  - `--fontforge-os2-defaults` and `--snap-component-transforms` are byte-identical no-ops
    for ComicRelief. Its .sfd states every OS/2 field those flags fill, including
    OS2XHeight 1105 and OS2CapHeight 1554.
- Note: their runs/ were rewritten at 22:31-22:32 BST, while this verification was
  running, by someone re-running their probes/rerun.sh. I did not run it. Their contents
  still equal mine.

## 2. Verdicts on proposed changes

**Edit "FSType 0" (RussoOne-Regular): KEEP.**
- The source states `FSType: 4` (line 18). The edit overwrites a stated value, and it
  does so openly: the body says so.
- It is minimal: one line.
- `value_derived_from` is honest. binary_facts.txt shows:
  - The hg binary is sha1 a1a8bff384a0, FFTM, fsType 4. It is byte-identical to
    google/fonts 90abd17b4.
  - 8ccda7bf7 changed the raw head, OS/2 and cmap tables. The only OS/2 field that changed
    is fsType. The cmap mapping is unchanged. HEAD equals 8ccda7bf7.
- No fidelity explanation is possible: FontForge's own export of this source carried 4.
- The landed config.yaml runs no gftools fix step, so the build cannot zero fsType on its
  own.
- The body's claims check out. The OFL.txt in the same package says "embedded" (line 21)
  and "embed" (line 49).

**Converter change (new ComicRelief underline rule): REVISE the spec. The classification
stands.**
- They missed that the .sfd was written by FontForge >= 20200314. Its header is
  `SplineFontDB: 3.2`, which sfd.c emits from 20200314 on, not at 20190317. It also uses
  the OS2XHeight/OS2CapHeight keywords.
- That FontForge's own TTF export writes `putshort(upos + uwidth/2)`, with `real`
  operands (tottf.c at 20190317, 20200314 and 20230101). For -185/175 that is
  (int)(-97.5) = -97.
- So the source's own exporter and the release's actual toolchain (sfdLib 2.0.0.post0 +
  ufo2ft 3.4.1, otRound) agree on -97. The row is converter-fidelity under the strict
  FontForge definition, not only relative to sfdLib.
- Their spec, `otRound(pos + width/2)` with a missing width read as 0, matches neither
  model at the edges:
  - sfdLib applies the shift only when both values are non-zero (parser.py:1557). For
    0/50 it keeps 0; FontForge and their rule give 25.
  - FontForge truncates toward zero; otRound rounds half up. For odd width with
    pos + width/2 > 0 they differ, e.g. trunc(2.5) = 2 but otRound gives 3.
- Recommendation: specify it as FontForge's >= 20190317 exporter rule,
  trunc(pos + width/2) in real arithmetic (i32: `(2*pos + width) / 2` with Rust's
  truncating division). Make it a vintage of `--fontforge-underline-position`
  (2017 = minus, 2019 = plus) rather than an sfdLib-named filter, so every converter flag
  stays a FontForge-fidelity flag. All three rules give -97 for both styles, so the gate
  result is unchanged.
- Their "-98 naive i32" warning is correct: -185 + 175/2 = -98.

**Flag changes (ComicRelief-Regular and -Bold: drop `--fontforge-underline-position`,
add the new rule): KEEP.** This is subject to the spec revision above and to per-family
overrides in tools/recipe.py and baseline.sh.

## 3. Classification checks

| row | their class | check |
|---|---|---|
| ComicRelief-{R,B} post.underline_position [-97, -272] | converter-fidelity | agree. The release was built from this exact source state (METADATA commit 856315f = tag v1.2; head.created = CreationTime), so it is not provenance. |
| ComicRelief-Bold OS/2.us_weight_class [700, 400] | converter-fidelity (in progress) | agree. It persists at ca43adc, since it is the fontc gap (issues/fontc-static-weight-class.md). |
| RussoOne OS/2.fs_type [0, 4] | source-edit-from-release | agree (see 2). |
| RussoOne OS/2.sx_height [530, 500] | converter-fidelity (in progress) | agree. The oracle matches 530/530 and 700/700, and the row closes at ca43adc. |
| Tuffy-{Regular,Italic} OS/2.fs_type [8, 0] | provenance | agree, with more evidence (below). |

Tuffy detail:
- Both .sfd variants state `FSType: 0`.
- The hg FontForge export (FFTM) has fsType 0 and carries the .sfd's garbage OS/2 script
  metrics verbatim: sub 0/2/0, strike 12312/-16224.
- The v1.272 release (ebcdfd2bb) has no FFTM. Its metrics are em-fraction defaults:
  - 1331/1228/153/716 = 0.65/0.6/0.075/0.35 x 2048, truncated;
  - strike 50/300.
- So it came from another tool, not from FontForge's export of this .sfd.
- 8 is Editable Embedding, the Glyphs.app default. glyphsLib's custom_params.py and fontc
  apply it when a source states no fsType. That is consistent with a tool default, not an
  authored value; this is an inference.
- `setfield FSType 8` would reproduce the release, but it discards a stated 0 and would
  fail googlefonts/fstype. It is the tuffy unit's decision.

## 4. Pairing

The pairing is correct for all 5 styles. release_facts.py, underline_rules.py and
baseline.sh read exactly the families.tsv source and shipped path. The plain Tuffy .sfd
was read for information only.

## 5. Missed or inaccurate

- The SFD 3.2 / FontForge >= 20200314 evidence (section 2) was missed. It matters because
  it puts the ComicRelief fix inside FontForge fidelity.
- underline_rules claim: "every FFTM release follows pre-2019" is inaccurate. The 4
  Puritan styles (FFTM 2010-04-29) match no rule from the unmodified source (-146). Only
  the puritan scaleem edit reconciles them.
- baseline/{ComicRelief-*,RussoOne-Regular}.gate.txt came from an older flag order
  (`--fontforge-os2-defaults` last) and gate f5cb410. Under the current baseline.sh and
  gate cd4f827 the rows are the same.
- Scope: comicrelief is not in the list of googlefonts repos Felipe was given.
  `git ls-remote` of googlefonts/comicrelief asks for credentials, so it is not public.
  Upstream main is at V1.210 (526aa02, 2025-05-07) and now converts its .sfd with
  FontForge itself. Whether to re-land it at all is Felipe's call.
- FINDINGS.md still does not exist.
- No rows opened; no styles uncovered.

## Rerun

    sh /home/fsanches/compartilhado/sfd-reland/investigations/small/verify/rerun.sh
