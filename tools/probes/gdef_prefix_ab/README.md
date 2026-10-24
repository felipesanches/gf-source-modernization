# Does a TTF-reader conversion need the GDEF GlyphClassDef prefix?

Question (Simon on simoncozens/babelfont-rs#131, about "ttf: state GDEF's glyph classes in the
features"): with the reader setting glyph categories ("ttf: read glyph categories"), is the
GlyphClassDef feature prefix still needed for the compiler to keep the release's GDEF?

Converter A/B: branch 2026-10-22 (58eedc8) as published, against the same tree with only the call
that inserts the GDEF prefix removed (scratch worktree, one commit, built with
tools/build_babelfont.sh). The 28 binary-only families landed from 2026-10-22 were re-landed in
scratch with the variant:

    BF_TREE=<variant> TABLES=families-binary.tsv OUT=<s>/repos LANDED=<s>/landed.tsv \
      SCRATCH=<s>/scratch LAND_ARGS=--unpublished-converter \
      sh tools/reland_all.sh 2026-10-24-no-gdef-prefix <the 28>
    python3 tools/probes/binary_to_source/gdef_classes.py <release.ttf> <variant build.ttf>

Result (verdicts-2026-10-24.tsv): 27 of 28 stay CLEAN. Carlito does not: all four styles block on
GDEF.glyph_classes ("a lookup filters on glyph class"; functional gate PASS). Its variant build
keeps only the 142 marks; the release's 2394 bases and 112 ligatures lose their class
(carlito-regular-gdef.txt), since none has an attaching anchor.

Why: for a .glyphs source, Glyphs.app, glyphsLib (`_build_public_opentype_categories`) and fontc
(glyphs2fontir `category_for_glyph_preliminary`, Base from anchors only) class a glyph Base or
Ligature only if it has an attaching anchor; only Mark comes from the category alone. A release
whose GDEF classes anchorless glyphs as bases or ligatures cannot keep them through categories; an
explicit `table GDEF { GlyphClassDef ... }` prefix, which all three honour, can.
