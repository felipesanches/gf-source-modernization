# Route (a): carry each release's TrueType hinting exactly

Decided by Felipe on 2026-11-05 (hub bottleneck.md, Decided). The functional gate's `hinting`
check (tools/functional_gate.py) is the acceptance test: a conversion is ready only when its
build has the release's prep, gasp, fpgm, cvt, maxp limits and head flag 3, every glyph
program on the same points, and identical hinted rasters.

## What exists today (checked 2026-11-05)

| piece                       | state                                                                                                     |
|-----------------------------|-----------------------------------------------------------------------------------------------------------|
| source format               | ufo2ft's `public.truetype.instructions` (formatVersion "1"): font lib holds cvt, fpgm, prep, maxp limits; glyph lib holds `assembly` and `id`, a hash of the glyph's TrueType points (fontTools HashPointPen) |
| Python build (fontmake)     | ufo2ft's InstructionCompiler compiles that key; a glyph whose `id` does not match its points gets no program (logged) |
| .glyphs -> UFO (glyphsLib)  | master userData -> font lib, layer userData -> glyph lib (glyphsLib builder/user_data.py)                   |
| on-curve points, Python     | ufo2ft keeps every on-curve point by default (`dropImpliedOnCurves=False`)                                 |
| on-curve points, fontc      | path_builder.rs makes every implied midpoint an explicit point (kurbo cannot omit one); write-fonts `simple_glyphs_from_kurbo` then drops every exact midpoint on-curve, explicit or not (write-fonts 0.55 glyf/simple.rs) |
| hinting, fontc              | none: no fpgm, prep, cvt or glyph programs                                                                 |
| TTF -> .glyphs (babelfont)  | writes every implied on-curve as an explicit node; reads no instructions                                   |

So the release's own exact-midpoint on-curves (which its programs address) are lost by
fontc, and babelfont adds points the release did not have: 2490 of 5318 instructed glyphs in
18 sampled fonts differ (points-2026-11-05.txt).

## Measured 2026-11-05: the hinting goes in its own file, applied after compiling

`roundtrip.py` (output `roundtrip-2026-11-05.txt`) writes each of 20 instructed release fonts
(Actor, Cantora One, Forum, Lobster Two x4, Quattrocento x2, Share x4, Stalinist One, Tuffy x2,
Volkhov x4) to a UFO that keeps the release's own points, then builds it two ways:

| route                                                                    | gate `hinting` |
|--------------------------------------------------------------------------|----------------|
| ufo2ft compiles `public.truetype.instructions` from the UFO libs         | 0 of 20 pass   |
| ufo2ft compiles the outlines; `hinting_file.py apply` adds the hinting   | 20 of 20 pass  |

Why the lib route fails, and cannot be fixed in the source alone:
- ufo2ft recalculates `maxp.maxSizeOfInstructions` from glyph programs; releases state larger
  values (Stalinist One 2411, its fpgm size; ufo2ft 138): 16 of 20.
- the device-metric tables `hdmx`, `LTSH`, `VDMX` have no source form; FreeType's v35
  interpreter takes advances from `hdmx` (Actor: Ntilde 6 px at 9 ppem in the release's
  `hdmx`, 7 px without it; the bitmaps are identical). Of the 233 instructed release fonts, 64
  have `hdmx`, 61 `LTSH`, 49 `VDMX`.
- ufo2ft sets ROUND_XY_TO_GRID on every component; some releases do not (Tuffy Regular, 534
  composites), which moves hinted composites.
- and a .glyphs source cannot carry the libs at all: glyphsLib drops every `public.*` userData
  key, and fontmake runs it in minimal mode, which skips layer userData.

So the source repository carries one text file per font, `hinting_file.py`'s format: fpgm,
prep (assembly), cvt, gasp, the maxp limits, head flag 3, hdmx, LTSH, VDMX, each glyph's program
(assembly) with ufo2ft's point hash `id`, and the hinting-relevant component flags. A builder
operation applies it to the compiled font and refuses any glyph whose points do not hash to
its `id`.

The points still have to be the release's. `midpoints.py` (`midpoints-2026-11-05.txt`): in
212 of the 233 instructed release fonts, 87,730 of 246,455 instructed simple glyphs have at
least one explicit on-curve point at the exact midpoint of its off-curve neighbours (253,217
points). fontc drops every such point (write-fonts `is_implicit_on_curve`); fontmake keeps them
(ufo2ft `dropImpliedOnCurves=False`; fontc_crater runs fontmake with `--drop-implied-oncurves`
to match fontc, googlefonts/fontc#336). The toggle was asked for upstream on
googlefonts/fontc#478 (dropping such points "could be undesirable ... because that would mess
with hinting"; "Maybe this behaviour should have an on/off toggle").

## Work, in order (revised 2026-11-05)

1. **Hinting file and builder operation.** `hinting_file.py` is the prototype (extract,
   apply). As gftools-builder operations, in Python gftools and in gftools-rust, with the same
   config key; when a font has a hinting file, no autohinting and no `fix` hinting changes.
2. **babelfont-rs TTF reader (an import fix):** keep the release's point structure (omit
   implied on-curves, keep explicit ones, keep contour starts). The extraction of the hinting
   file belongs to the conversion (land.py), from the release binary.
3. **fontc:** the #478 toggle, keeping the source's explicit on-curve points (the IR has to
   know which on-curves the source had; today path_builder makes every implied one explicit).
4. **Python check end to end** on a converted repository (fontmake keeps the points), then the
   same with fontc once (3) exists.
5. **Re-land** the repositories that fail `hinting`; the gate decides each.

## First plan (2026-11-05 morning, superseded above)


1. **Representation.** Store the hinting in the .glyphs source in the format both pipelines
   can read: `public.truetype.instructions` in master userData (font level) and layer userData
   (per glyph); gasp as the "gasp Table" custom parameter. No new format, no new file.
2. **babelfont-rs (TTF reader, an import fix):** keep the release's point structure (omit
   implied on-curves, keep explicit ones, keep the start point) and read fpgm, prep, cvt, maxp
   limits and glyph programs into (1). A reader change, no filter. Where the points are
   lost (simoncozens/babelfont-rs 622ed1fd, babelfont/src/convertors/ttf.rs): a simple glyph is drawn
   through skrifa's outline pen into PathBuilder, and the pen reports every implied on-curve
   as a `quad_to` end point, so it becomes a node. Reading the glyf points, flags and
   contour ends directly (as the composite branch already parses components) keeps them.
3. **Python check first:** build a converted hinted release with fontmake (gftools builder,
   `autohintTTF: false`) and run the gate. This proves (1) and (2) before any fontc work.
4. **fontc:** keep source on-curve points (carry "explicit" through the IR so only the
   midpoints fontc inserted are dropped) and compile `public.truetype.instructions` as ufo2ft
   does, including the `id` check. Parity with fontmake, so crater can compare.
5. **gftools-builder (Rust and Python):** no autohinting and no `fix` prep/gasp rewrite for a
   font that carries its own hinting; whatever config key this needs must be valid in both.
6. **Re-land** the 104 published repos that fail `hinting` as follow-up commits, and the held
   unpublished ones; the gate decides each.
