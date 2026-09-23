# Glyphs 2 sources through gftools-builder3's static path

Question: why does alexeiva/play's Play.glyphs (Glyphs 2) build, as statics, to a font
with the wrong codepoints and only one of its two styles?

`sources/Min.glyphs` is a two-master, two-instance Glyphs 2 file with `A` (`unicode =
0041;`) and `endash` (`unicode = 2013;`), the Bold instance omitting
`interpolationWeight` as Glyphs 2 does at 100.

    sh run.sh [workdir]

`RESULT.txt` (three runs, gftools-builder3 e851b8b):

- variable build (fontc's own Glyphs reader): U+0041 U+2013 -- correct
- static build (`buildVariable: false`, read through glyphslib-rs 0.2.7): U+0041
  **U+07DD**, and only ONE of Min-Regular/Min-Bold is written, a different one per run

Causes, both in glyphslib-rs:
1. `CommaHexStringVisitor::visit_u64` formats the integer 2013 as hex and parses it as
   hex, a no-op: fix on branch `fix-v2-unquoted-hex-unicode`.
2. an omitted instance `interpolationWeight` defaults to 0, not 100, so both instances
   sit at weight 0 (babelfont writes `axesValues = (0)` for both): fix on branch
   `fix-instance-interpolation-default`.
