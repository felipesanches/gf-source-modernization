# puritan -- not provenance: FontForge 20100501's em change, reproduced

**Model**: Claude Opus 5.5 (investigation, adversarial verification, and this write-up)
**Date**: 2026-09-23. Pins: babelfont gf-sfd-conversion ca43adc (landing), gftools-builder3
e851b8b (fontc 1.0.0), google/fonts b5efa9c32e8f.

Written from the two agents' structured results (the harness refused their report files).
Where the verifier corrected the investigator, the correction is stated.

## Conclusion

Every earlier note filed Puritan as provenance ("a source generation this repo no longer
holds"). It is not. The release is exactly the four `.sfd` in googlefontdirectory-hg, run
through the family's **original** `src/generate.py` (googlefontdirectory-hg `e6ab8ab47`;
the script at `52f780bc` is a later rewrite) under **FontForge 20100501**: export at em
1000, then `f.em = 1024`, then the `.ttf`.

- The release's `FFTM` FFTimeStamp, 2010-04-29 03:43:27, equals `LibFF_ModTime`
  1272512607 in `fontforge_full-20100501.tar.bz2` (sha256
  `ee4928b0df7480c31a422645854d9f3f4f6718dd423b6885bd33e87a8a6edd79`).
- `tools/ff_scale_em.py` ports what `f.em = 1024` executes in that version, in single
  precision (`real` was float in a default 2010 build). The em splits by integer
  division, 820/204 (`python.c`); widths are truncated (237/237 match, `rint` only
  107/97/113/113); each control point's OFFSET from its rounded point is rounded
  (`SplinePointRound`), and plain per-point rounding matches only about 40% of glyphs.
- The scaled `.sfd` reproduces the released glyf point for point: 237/237 glyphs and
  237/237 advances in each of the four styles. The verifier confirmed it with its own
  independent comparison (`verify/cmp_glyf.py`), from a fresh extraction.

## The Italic 1-unit residual

In all four styles each composite's cached bounding box stayed as its UNSCALED components
plus a SCALED offset (verifier's correction: not an encoding-order effect; Regular
Scaron's header xMin/xMax 41/450 is the unscaled S). `tools/stale_composite_bbox.py`
predicts every such header (3/3/8/8). Only Italic is affected in the tables, because
Scaron is its tallest glyph: its outline reaches 881 while its header says 864, so the
font bounding box -- and the offset-mode Win and hhea ascent -- is Aring's 880. The
release clips Scaron by one unit.

Two ways to close it, both verified: state 880 absolutely (with the offset flag cleared),
or keep offset mode with -1. The landing uses the absolute form, following the precedent
of `OS2WinDescent 627` / `OS2WinDOffset 0` in the published repositories, and says in the
commit that it reproduces the clip. Dropping those two commits leaves Italic at the value a
fresh FontForge export would give (881) and 2 blocking rows.

## Result (landed)

`sfd-reland-repos/puritan`: import, template, `Scale the em to 1024 as src/generate.py
did`, `OS2WinAscent 880, as the release carries`, `HheadAscent 880, as the release
carries`, convert. **0 blocking rows in all four styles**; `tools/verify_landed.py`
VERIFIED. Before the edits: 19/19/20/20.

## Notes for later

- The underline is written as integers by the edit (`-136`, `20`) because babelfont's
  `parse_metric!` drops a non-integer value entirely; FontForge exports the same bytes
  either way. `../../../sfd-batch6/issues/babelfont-italic-angle-rounded.md` now covers it.
- Three `.sfd` were edited after the build (googlefontdirectory-hg `e15966610`, FSType 1 to
  0); google/fonts `8ccda7bf7` made the same change to the binaries, so no row results.
- The scaled `.sfd` keeps em-1000 TrueType instructions, cvt, prep and fpgm; the converter
  ignores them and the release regenerated them with `autoInstr`.
- `scaleem` refuses sources with kerning, anchors, PostScript hints, BASE or MATH, which the
  port does not scale; it is proven for Puritan only.
- The prior notes that call Puritan provenance are wrong on this point:
  `sfd-batch6/B6-RESIDUALS-2026-09-22.md`, `sfd-batch6/WHATS_NEEDED.md`,
  `sfd-batch5/PROVENANCE-NOT-CONVERSION-2026-09-23.md`.

## Rerun

    cd /home/fsanches/compartilhado/gf-source-modernization
    PY=/home/fsanches/compartilhado/gftools/venv/bin/python3
    $PY tools/land.py puritan --rebuild          # plans/puritan.json; gates all four styles
    $PY tools/verify_landed.py puritan
    $PY investigations/puritan/tools/verify_scaled_points.py <scaled.sfd> <release.ttf>
