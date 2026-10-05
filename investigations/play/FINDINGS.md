# play -- the release is not built from the .sfd at all

**Model**: Claude Opus 5.5 (investigation, adversarial verification, and this write-up)
**Date**: 2026-09-23. Pins: babelfont gf-sfd-conversion f725e6a, gftools-builder3 e851b8b
(fontc 1.0.0), google/fonts b5efa9c32e8f.

The subagent harness refused to let the investigating agents write report files, so this
file is written from their two structured results. Where the verifier corrected the
investigator, the correction is what is stated here.

## Conclusion

google/fonts ships Play **v2.101**, built from the Glyphs source `sources/Play.glyphs` of
**alexeiva/play** (Alexei Vanyashin / Cyreal, the v2 author), tip `d84ad58`. The shipped
fonts differ from that repository's committed `fonts/ttf/*` only in `head.modified` and
`head.checkSumAdjustment`, and match its unhinted Glyphs.app export (`f17f03f`) in every
non-hinting table and all 1150 glyphs' coordinates. `m4rc1e/play` `3565c8a` is a fork with
the identical tree (`57de73f`, checked independently); alexeiva/play is canonical.

The googlefontdirectory-hg `.sfd` files are **v1.001/v1.002 (2011)**. They lack 133 of the
shipped codepoints and the whole v2 feature code, and 218 of 231 outlines differ. No `.sfd`
edit short of replacing the design reproduces v2.101, and no FontForge-exporter rule of any
vintage produces the missing glyphs or the Glyphs-derived OS/2, hhea, GSUB and GDEF.

So the `.sfd` route cannot satisfy criterion (A) for play: its conversion commit would
reproduce v1.002 at best.

## Measurements

| style | blocking rows vs v2.101 | of which |
|---|---:|---|
| Play-Regular | 220 | 133 codepoints missing, 65 renamed/redrawn, 22 others |
| Play-Bold | 233 | 133 missing, 78 renamed/redrawn, 22 others |

Against v1.002 the Bold `.sfd` reproduces the outlines and advances exactly. The Regular
`.sfd` does not match v1.002 either (Version 001.001 vs 1.002, vendor `PT  ` vs `PLAY`,
typo/hhea descender +220 vs -220, 1005 vs 1007 glyphs, U+044A/U+0457 outlines).

The earlier batch-6 figure of "16 rows" (`sfd-batch6/B6-RESIDUALS-2026-09-22.md`) was
measured after the old pipeline had copied the release's cmap and heights into the build;
the true gap is 220/233.

## Other Play sources, to keep documented (preserve-old-repos policy)

- googlefontdirectory-hg `ofl/play/src/Play-{Regular,Bold}-TTF.sfd` at `52f780bc9d19`
  (v1; the `-TTF` names suggest they were made by opening a TTF in FontForge)
- librefonts/play `0d4e17b` (2014): byte-identical copies of those `.sfd` plus TTX dumps
- google/fonts `874c7ceb1` (2016-10-31, Alexei Vanyashin) added
  `ofl/play/Play-{Regular,Bold}.glyphs` (Glyphs 1 era), `Play-{Regular,Bold}.vfb` and
  `Play-Bold.vfbak`; `e36afc756` deleted them. The `.vfb` are probably the FontLab masters.

All three upstream repositories are now in the repo archive
(`alexeiva/play.git`, `m4rc1e/play.git`, `librefonts/play.git`).

## Decision for Felipe

`googlefonts/play` was created empty for an `.sfd` re-land. The re-land that can meet the
criteria is instead: push **alexeiva/play**'s history into `googlefonts/play`, point
METADATA.pb at it (commit `d84ad58`, `sources/Play.glyphs`, a config that builds it), and
document the v1 `.sfd`, the librefonts mirror and the 2016 `.glyphs`/`.vfb` as original
sources. That puts play on the modern-upstream track, not the conversion track.

Two local notes: the google/fonts working copy has a commit `51c6a423f`, on local branches
such as `add-legacy-sources-config-overrides`, that points play's METADATA.pb at
googlefontdirectory-hg `52f780bc9d`, and an `upstream_info.md` (`8b0a1d0f5`) saying no
canonical upstream exists. Both are wrong for v2.101 and must be kept out of any PR.

## Loose ends found on the way

- Building the Glyphs source with builder3 leaves 62 rows (`probes/modern_route_gate.sh`):
  U+FB00/FB03/FB04 have no unicode in `Play.glyphs` (Glyphs.app assigns them at export), and
  the underline position, one hmtx row, GDEF classes and panose bWeight have likely
  Glyphs.app-export explanations not yet checked against Glyphs.app.
- builder3 `e851b8b` returns 0 when the Play-Bold target is never produced (the known
  silent no-op; `GoogleFonts/drafts/gftools-builder3-silent-noop.md`).
- FontForge's 2012 exporter (`tottf.c` ~l.2968) picks the hhea descender offset using the
  ascender's flag; master fixed it. A `.sfd` with `HheadAOffset != HheadDOffset`
  reproducing a pre-fix export would need a converter rule. No effect on play.

## Rerun

From `gf-source-modernization/investigations/play/` (full table in `probes/README.md`):

    M=/home/fsanches/compartilhado/upstream_repos/repo_archive/m4rc1e/play.git
    bash ../../tools/baseline.sh Play-Regular Play-Bold      # 220 / 233 rows, from the .sfd
    bash probes/release_vs_upstream.sh $M                    # the release is that repo's export
    bash probes/modern_route_gate.sh $M                      # the Glyphs route: 62 rows
    python3 verify/threeway.py <gate.txt> <release.ttf> <v1.ttf> <ours.ttf>
