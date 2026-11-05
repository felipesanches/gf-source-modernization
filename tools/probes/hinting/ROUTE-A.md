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

## Work, in order

1. **Representation.** Store the hinting in the .glyphs source in the format both pipelines
   can read: `public.truetype.instructions` in master userData (font level) and layer userData
   (per glyph); gasp as the "gasp Table" custom parameter. No new format, no new file.
2. **babelfont-rs (TTF reader, an import fix):** keep the release's point structure (omit
   implied on-curves, keep explicit ones, keep the start point) and read fpgm, prep, cvt, maxp
   limits and glyph programs into (1). A reader change, no filter.
3. **Python check first:** build a converted hinted release with fontmake (gftools builder,
   `autohintTTF: false`) and run the gate. This proves (1) and (2) before any fontc work.
4. **fontc:** keep source on-curve points (carry "explicit" through the IR so only the
   midpoints fontc inserted are dropped) and compile `public.truetype.instructions` as ufo2ft
   does, including the `id` check. Parity with fontmake, so crater can compare.
5. **gftools-builder (Rust and Python):** no autohinting and no `fix` prep/gasp rewrite for a
   font that carries its own hinting; whatever config key this needs must be valid in both.
6. **Re-land** the 104 published repos that fail `hinting` as follow-up commits, and the held
   unpublished ones; the gate decides each.
