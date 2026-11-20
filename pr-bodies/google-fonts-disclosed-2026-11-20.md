Title: Source metadata: Averia Libre, Averia Sans Libre, Averia Serif Libre, Sansation

Body:
Metadata only, no binaries change. One commit per family (METADATA.pb `source` block + upstream_info.md).

No source of these families was ever published (googlefontdirectory-hg and librefonts hold only the fonts, subsets and TTX dumps of them), so each now points at a new https://github.com/googlefonts/<family> repository: the shipped fonts imported unmodified, the Unified Font Repository template, then the conversion to `.glyphs` with babelfont-rs's TTF reader.

Every build was rebuilt from the recorded commit and checked against the shipped fonts with https://github.com/felipesanches/gf-source-modernization (table gate and functional gate, hinting included). Known differences, disclosed in each upstream_info.md and README:

* All four: the releases kern with a legacy `kern` table; the builds kern through GPOS, which is how fontc builds kerning. HarfBuzz shapes every kerned pair alike, except Averia's pairs with the soft hyphen (U+00AD).
* Sansation Light Italic: the release flags it italic with an italic angle of 0, which a Glyphs source cannot state to fontc 1.0.0; and its post table names two glyphs `ffi`, the second is `ffi.1` in the source.

Assisted by an AI agent (Claude Opus 5.5)
