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

## 2026-10-28: the prefix reverted; the classes become a source workaround where they matter

Felipe agreed with Simon: 47f99442 is reverted on both fork branches (2026-10-22 ed59a63a,
2026-10-23 50ea5d2d), and the 35 unpushed repositories that cited the old heads were re-landed
(logs/reland-2026-10-28-gdef-revert). Three fail without the prefix: Carlito (as above), Sansation
(its GDEF classes every glyph base, commaccent U+0326 included, and no glyph mark; the build has
no GDEF, HarfBuzz classes commaccent a mark, and the kerning skips it: 1 class difference shaping
reads) and Jomolhari (the same shape: all 3333 glyphs base, 88 combining marks among them; 21955
shaped runs differ without the table).

`gdef_needs_prefix.py` asks whether a cheap rule on the release alone (the classes a compiler
derives from categories and anchors differ, and a lookup filters on class or the GDEF has no
marks) predicts that: no. needs-2026-10-28.txt flags Sansation, Black And White Picture, Nanum
Pen Script and Dongle; the last three pass the gates without the prefix (Carlito's release is not
in google/fonts, the script skips it). So the decision is the gate's, recorded per family:
`gdef_classes_fea` in plans/carlito.json, plans/sansation.json and plans/jomolhari.json makes tools/land.py state the
release's classes as a `table GDEF { GlyphClassDef ... }` feature prefix in the source
(tools/workarounds.py gdef_classes_fea), noted in the convert commit. `gdef_fea_check.py` showed it
writes, for both, the same statement the reverted reader wrote (the repositories' .prev
generation still holds it):

    /home/fsanches/compartilhado/gftools/venv/bin/python3 -I tools/probes/gdef_prefix_ab/gdef_fea_check.py <dir with Carlito-Regular.ttf and Sansation-Regular.ttf>
    /home/fsanches/compartilhado/gftools/venv/bin/python3 -I tools/probes/gdef_prefix_ab/gdef_needs_prefix.py
