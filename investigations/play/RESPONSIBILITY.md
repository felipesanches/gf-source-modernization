# play, Glyphs route: which tool owns each remaining difference

**Model**: Claude Opus 5.5. **Date**: 2026-10-02.

## The pipeline, read from the code

`sources/config.yaml` says `buildVariable: false`; Play.glyphs has two masters. So
gftools-builder (gftools-rust ade8776, `recipe_providers/googlefonts.rs`
`build_a_static`) builds each static as:

1. `babelfont::load` (babelfont 0.2.2): glyphslib-rs reads the Glyphs 2 file and
   `upgrade_in_place()` turns it into Glyphs 3 (`glyphslib/src/upgrade.rs`); babelfont
   converts that to its own model (`convertors/glyphs3.rs` `_load`).
2. `instantiateSource` (`operations/instantiate_source.rs`): babelfont
   `SetDefaultLocation(instance.location)` + `DropVariations` (one master, no axes, **no
   instances**).
3. The slimmed font is written back as a Glyphs 3 file (`buildsystem/output.rs`
   `to_filename`, babelfont `save`), and `fontc` (1.0.0: `glyphs-reader` +
   `glyphs2fontir` + `fontbe`) compiles that file.
4. `fix`. No autohint step (see 10).

`probes/intermediate_glyphs/` rebuilds step 1-3's file (`cargo run --release -- Play.glyphs out/`).

fontmake 3.11.1 / glyphsLib 6.12.7 / ufo2ft 3.7.0 on the same Play.glyphs
(`fontmake -g Play.glyphs -o ttf -i`) was used as the reference for what glyphsLib does;
`probes/residual_items.py release=... fontmake=... build=...` prints the table below.

| # | release | fontmake | gftools-builder + PR #4 | owner |
|---|---|---|---|---|
| 1 | latn: 19 features; scripts DFLT cyrl grek latn | latn: ccmp; DFLT latn | same as fontmake | fontc |
| 2 | acutecomb adv 0, x -299..-100 | adv 0, x 100..299 | same as fontmake | fontc |
| 3 | Gcommaaccent, brevecombcy, nonmarkingreturn | uni0122, uni0306.cy, CR | same as fontmake | fontc |
| 4 | U+FB00/FB03/FB04 -> ff/ffi/ffl | unmapped | unmapped | fontc |
| 5a | Bold usWeightClass 700 | 700 | 400 | fontc, plus gftools-rust (fixed) |
| 5b | Regular IDs 4/6 "Play Regular"/"Play-Regular" | same | "Play"/"Play" | glyphslib-rs (fixed) |
| 6 | panose bWeight 5 / 8 | 0 | 0 | fontc |
| 7 | post.underlinePosition -75 | -100 | -100 | fontc |
| 8 | GDEF 1.0, MarkAttachClassDef | GDEF 1.2, mark filtering sets | same as fontmake | fontc |
| 9 | U+0122: 43 points (Bold 42) | 45 | 44 | fontc |
| 10 | ttfautohinted | unhinted | unhinted | gftools-rust (fixed) |

fontc follows glyphsLib for items 1-4 and 6-8. Glyphs.app does something else at export,
so reproducing Glyphs.app in these items is a fontc change, not a glyphsLib-parity fix.

## Fixed now (non-fontc)

- **5b**: glyphslib-rs `glyphslib/src/upgrade.rs` `glyphs2::Master::to_glyphs3`. A
  Glyphs 2 master that omits `weight` (Glyphs 2 writes nothing for Regular) deserializes
  with `weight == ""`. That empty particle was pushed and joined into an empty Glyphs 3
  master name. fontc's `names()` (`glyphs2fontir/src/source.rs`) takes the typographic
  subfamily from the default master name, so ID 4/6 became "Play". Branch
  `fix-v2-master-name-omitted-weight` ed4fc2a (off upstream main b602b59).
- **5a, gftools-rust part**: `operations/instantiate_source.rs`. `DropVariations` clears
  `font.instances`, so the static's own instance (`weightClass = Bold` -> 700, `isBold`)
  never reaches the compiler. fontmake builds the static from that instance. Branch
  `instantiate-keep-instance` 7f6eccd keeps the instance at the instantiated location.
  This has no effect until fontc reads it (below).
- **10**: `recipe_providers/googlefonts.rs` `build_a_static` has no autohint step, while
  `instantiate_a_static` always autohints and ignores `autohintTTF`. The Python builder
  autohints every static TTF (`autohintTTF`, default true, `--fail-ok`). Branch
  `static-autohint` 1ce8f5f adds `autohintTTF`/`ttfaUseScript` to both paths.
  The release's `--increase-x-height=13` (`TTFAutohint options` parameter, sources/build.sh)
  is not read by either builder.

PR bodies: `../../pr-bodies/glyphslib-rs-fix-v2-master-name-omitted-weight.md`,
`gftools-rust-instantiate-keep-instance.md`, `gftools-rust-static-autohint.md`.

## fontc-only, disclosed (fix later)

Paths are in googlefonts/fontc main 0fd2c16a (the shipped crates are 1.0.0).

1. **No automatic `languagesystem`s.** `glyphs2fontir/src/toir.rs` `to_ir_features`
   (via `FeatureWork::exec`, `glyphs2fontir/src/source.rs`) emits the file's prefixes,
   classes and features as they are. Play.glyphs has no `Languagesystems` prefix and all of
   its features are `automatic = 1`. At export, Glyphs.app writes an automatic
   `languagesystem` for every script in the font (release GSUB: DFLT, cyrl, grek, latn,
   each with all 19 features). Without them feaLib/fea-rs register features for DFLT/dflt
   only. A `script latn;` inside ccmp creates a latn that holds only ccmp, so Latin text
   never gets liga/smcp/c2sc/aalt/case. glyphsLib does the same (fontmake: DFLT + latn{ccmp}).
2. **Zero-width marks not shifted.** `glyphs2fontir/src/source.rs` `process_layer` sets
   `width: 0` for `is_nonspacing_mark()` glyphs (as glyphsLib does) but keeps the outline
   and anchors at the source x. Glyphs.app also moves them left by the old width:
   acutecomb width 399, x 100..299 in the source and -299..-100 in the release. Composite
   marks and mkmk positions move with it (rendering: 48/53 outlines; shaping base+mark).
3. **Production names from the bundled GlyphData.** `glyphs-reader/src/font.rs`
   `RawGlyph::build` takes `production_name` from `glyph_data.query` (Glyphs 3 GlyphData)
   when the file has none. Play.glyphs was written by Glyphs 2 (`.appVersion = "983"`),
   whose GlyphData gives Gcommaaccent, Kcommaaccent..., brevecombcy, nonmarkingreturn where
   Glyphs 3 data gives uni0122, uni0136..., uni0306.cy, CR. babelfont writes the
   intermediate as format 3 but keeps `.appVersion = "983"`. glyphsLib does the same
   (Glyphs 3 data).
4. **GlyphData Unicode values not assigned.** The same `RawGlyph::build` takes codepoints
   only from the file. Glyphs.app assigns GlyphData's Unicode values at export, so a glyph
   `ff`/`ffi`/`ffl` without `unicode` gets U+FB00/FB03/FB04. glyphsLib does the same as fontc.
5. **(5a) Single-master instance weightClass ignored.** `fontbe/src/os2.rs` (`Os2Work::exec`,
   `us_x_class`) takes usWeightClass from the `wght` axis default, else
   `static_metadata.misc.us_weight_class`, else 400. `glyphs2fontir` never sets
   `misc.us_weight_class`. Point axes are dropped (`fontir` `StaticMetadata::new`), so a
   static Glyphs source always builds 400. Already reported as
   `../../issues/fontc-static-weight-class.md`. Verified here: the intermediate with the Bold
   instance (`weightClass = 700`) restored, with and without a `wght` point axis, still
   builds 400. fontmake builds 700.
6. **PANOSE not derived.** `glyphs2fontir/src/source.rs` `StaticMetadataWork::exec` takes
   `panose` only from the instance or master custom parameter, else none (zeros). Glyphs.app
   fills bWeight from the weight class (Regular 5, Bold 8 in the release). glyphsLib/ufo2ft: zeros.
7. **underlinePosition.** `glyphs2fontir/src/source.rs` (`set_metric!(UnderlinePosition,
   underline_position, -100.0)`) -> `fontbe/src/post.rs` writes the parameter as is.
   Glyphs.app writes the parameter plus half the thickness (-100 + 50/2 = -75). glyphsLib/ufo2ft: -100.
8. **Mark filtering sets.** `fontbe/src/features/marks.rs` (`make_filter_glyph_set`,
   `USE_MARK_FILTERING_SET`) restricts generated mark/mkmk lookups with GDEF 1.2 mark
   filtering sets. Glyphs.app's export uses GDEF 1.0 mark attachment classes (lookup flags
   256/512/768). ufo2ft does the same as fontc. 0 classes differ that shaping reads.
9. **Cubic-to-quadratic.** `fontbe/src/glyphs.rs` `cubics_to_quadratics` (kurbo
   `cubics_to_quadratic_splines`): Gcommaaccent gets 44 points, the release 43 (Bold 42),
   fontmake's cu2qu 45. Same bbox. Each converter makes its own choice.
