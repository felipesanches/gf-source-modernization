# unifraktur -- adversarial verification

**Model**: Claude Opus 5.5 -- 2026-09-23

Unit: UnifrakturMaguntia-Book (repo googlefonts/unifraktur). Verdict: the 7 rows and
their causes hold. I reproduced every number with my own code, using the exporter source
that matches the release exactly. The fixes need refining (GPOS shell rule, naming, one
recipe flag), and I found 3 misses that the gate does not block on.

## Pins
- source: googlefonts/googlefontdirectory-hg @52f780bc, ofl/unifrakturmaguntia/src/UnifrakturMaguntia.sfd
  (sha256 2457ee9a...). It is the only .sfd in the family tree.
- release: google/fonts b5efa9c32e8f ofl/unifrakturmaguntia/UnifrakturMaguntia-Book.ttf (sha256
  d64afc05...). It is byte-identical to the TTF in the hg tree at 52f780bc.
- babelfont binary sha256 f96e0851... (f725e6a, built before ca43adc; same hash before and after
  my runs), gftools-builder3 e851b8b (fontc 1.0.0), diffenator3 1.1.4, table_gate.py cd4f827
  (sha256 008e7319...), baseline.sh sha256 c76a392f..., fontTools 4.61.1, uharfbuzz 0.53.3 /
  HarfBuzz 12.3.2.
- FontForge exporter: release tarball fontforge_full-20100501.tar.bz2 (sha256 ee4928b0...).

## 1. Reproduction (fresh copies made from the unmodified source; builds run one at a time)
| run | change | rows |
|---|---|---|
| 00 | unmodified | 7 (same rows and values as baseline/UnifrakturMaguntia-Book.gate.txt) |
| 02 | OS2WinDescent 512/OS2WinDOffset 0, HheadDescent -513/HheadDOffset 0 (stand-in) | 5 (the 2 vmetric rows close; none opens) |
| 03 | 02 + OS2CapHeight 1409, OS2XHeight 1095 (stand-in) | 3 (GPOS only) |
| 03+graft | the release's own GPOS bytes grafted onto build 03 | "0 blocking table difference(s), 3 stale"; d3 0 glyphs |
Their rows_after is reproduced. My graft copies the release's own table rather than
their shell built from our GSUB, so it is an independent control.

Shaping, from my own shape_check.py (153 cmap'd L/N bases x 9 marks, plus each mark alone = 1386 texts):
build as-is: 1317 of 1386 differ in ltr; with the graft: 0 in ltr and 1386 in ttb.

## 2. Exporter provenance (strengthens their claim)
The FFTM FFTimeStamp is 1272512607, and the 20100501 tarball's libffstamp.h gives LibFF_ModTime
1272512607, an exact match. cd438ca99d76's own libffstamp.h says 1272500371, so cd438 is not
literally the build. Their line citations still stand: tottf.c, splinefont.c, splineutil.c,
splineutil2.c, splineorder2.c, lookups.c, tottfgpos.c and ttfspecial.c are byte-identical
between the tarball and cd438. FFTM sourceCreated and sourceModified equal the .sfd's
CreationTime and ModificationTime.

## 3. Rows (my independent port: indep_probe.py, not their probes)
- hhea.descender, OS/2.us_win_descent -- converter-fidelity: AGREE. The .sfd states offsets
  (HheadDOffset 1, OS2WinDOffset 1). J's lowest on-curve point is implied (flag 128) at -495.5;
  floor gives the head.yMin of -496, and win = 496+16 = 512. The true curve minimum is
  -497.5805; the int() in sethhead makes it -497, so hhea = -513. babelfont's round() gives
  514/-514. The 2010 composite path (dumpcomposite ->
  SplineCharLayerQuickBounds) is also on-curve only, which matches the proposal. ee15007274e9 (2014-09-16)
  is confirmed as the change that added control points.
- OS/2.sx_height -- converter-fidelity (in progress): AGREE. 17 distinct round tops, 1095.18 -> 1095
  under both rules.
- OS/2.s_cap_height -- converter-fidelity: AGREE. None of the 26 A-Z tops is flat, and 25 are
  distinct (I and J = 1503.0941). The 2010 mean is 36635.1018/26 = 1409.04 -> 1409; the
  post-4d34d21ef866 mean is /25 = 1465.40. My port also reproduces the other 5 pre-2012 styles
  exactly: UnifrakturCook-Bold 319/485, HerrVonMuellerhoff 269/644, Miama 265/894, Nosifer and
  NosiferCaps 925/854.
- GPOS.script_list/feature_list/lookup_list -- the cause is right: SFScriptsInLookups
  deliberately ignores gpos. These rows are toolchain fidelity, not babelfont. My check:
  a kern block holding only `script`/`language` statements also yields NO GPOS from
  fontc 1.0.0 (runs/05). Blocking is correct, not gate-arbitration, because the shell
  suppresses HarfBuzz's fallback positioning (1317 differing ltr texts without it).

No .sfd edits were proposed. The stand-ins leave every value the source states in place
(the offsets stay offsets; the .sfd states no x-height or cap height).

## 4. Revisions to their proposals
- GPOS shell rule: languages are NOT shared between the tables. SFLangsInScript (lookups.c:375-425) is
  per table. A script with no lookups in a table gets only a dummy DEFAULT_LANG (dflt);
  scripts are the UNION of both tables and go into both, even when both tables have
  lookups. Their "same scripts and languages" rule, and their probe's copying of GSUB
  LangSysRecords, would emit languages FontForge never wrote. This font is unaffected, since
  it has only dflt.
  Reproducing the shell deliberately turns HarfBuzz's fallback mark positioning back off.
  Deciding that belongs to Felipe.
- Vmetric rule: it must say which vintage to assume when the release has no FFTM (Play,
  Tuffy, Corben, ComicRelief).
- File name: calling it "a METADATA.pb matter, not a source edit" is incomplete.
  babelfont (fontforge.rs ~L985) names the master from TTFWeight 400 -> "Regular". It stores
  the stated "Weight: Book" as postscript_weight_name and never uses it. The effect is
  nameID 2 Book->Regular, nameID 4 +" Regular", nameID 6 UnifrakturMaguntia->UnifrakturMaguntia-Regular.
  The gate accepts all of this, but it is a silent converter normalisation. METADATA.pb must
  follow the new names, and the PR must disclose them. Whether to make the rename visible is
  a policy call: a "Weight: Regular" .sfd edit would not change the build.

## 5. Missed (none of these is a blocking row)
- --add-legacy-duplicate-cmap misfires here. The .sfd itself maps U+00A0 to space (AltUni2)
  and has its own uni00AD. The harness's test (the release carries 00A0 and 00AD) therefore
  says yes, and the flag adds U+02C9->macron and U+2219->periodcentered, which the release
  lacks. table_gate cmap_blocking accepts gained codepoints and prints nothing. With
  DROP_FLAGS="--add-legacy-duplicate-cmap", the cmap is identical to the release (247/247)
  and the same 7 rows remain (runs/04). For this style the flag is not a fidelity flag.
- OS/2.fs_selection is 64 in the release and 192 in ours. The .sfd states OS2_UseTypoMetrics 1
  but OS2Version 3, and FontForge 2010 sets bit 7 only for version>=4 (tottf.c:3331-3337).
  The gate accepts it wholesale. It changes the HarfBuzz vertical advance (2121 vs 2120),
  and the line gap in apps that honour the bit (typo 2121 vs hhea 2120 / win 2119). Their
  unresolved note blames the vertical residue on glyf header bboxes only, but their own
  C-hhea513-nobit7 control shows bit 7 accounts for part of it (6225 -> 5232 ttb runs).
- "Only this one blocks because it is the only style with combining marks" is wrong as
  stated. Monoton (4), Smythe (2), Tuffy-Bold/BoldItalic (19) and UnifrakturCook-Bold (9) have
  marks too, but their shell is an empty GSUB. Correct statement: it is the only one of the 4
  empty-GPOS releases (Kristi, Lekton-Bold, Lekton-Regular, UnifrakturMaguntia-Book) with marks.
  The 19 empty GSUB / 4 empty GPOS census is confirmed.
- FINDINGS.md still does not exist in this directory.

## Rerun (S = scratch dir inv-unifraktur-verify; W = /home/fsanches/compartilhado/gf-source-modernization)
    git -C .../repo_archive/googlefonts/googlefontdirectory-hg.git show 52f780bc:ofl/unifrakturmaguntia/src/UnifrakturMaguntia.sfd > $S/orig.sfd
    TAG=unifraktur-verify SCRATCH=$S OUT=$S/runs/00-baseline bash $W/tools/baseline.sh UnifrakturMaguntia-Book
    # standin-vm.sfd / standin-vmh.sfd = sed of orig.sfd exactly as in the table above
    TAG=unifraktur-verify SCRATCH=$S OUT=$S/runs/03-standin-vmh SRC_OVERRIDE=$S/standin-vmh.sfd bash $W/tools/baseline.sh UnifrakturMaguntia-Book
    TAG=unifraktur-verify SCRATCH=$S OUT=$S/runs/04-drop-dupcmap DROP_FLAGS="--add-legacy-duplicate-cmap" bash $W/tools/baseline.sh UnifrakturMaguntia-Book
    python3 $S/indep_probe.py <any .sfd>                  # bounds + 2010/2012 height means
    $PY $S/shape_check.py <release.ttf> <built.ttf> [<built+graft.ttf>]
My probes (indep_probe.py sha256 ea0b7b2d..., shape_check.py sha256 984a70d1...) and my runs
exist only in scratch (/tmp, volatile). The task limited my writes to this file, so I did not
save them here. Copy them here if they are to be kept.
