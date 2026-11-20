Title: Source metadata: Beth Ellen, Krona One, Ovo, Pompiere, Short Stack, Sonsie One

Body:
Metadata only, no binaries change. One commit per family (METADATA.pb `source` block + upstream_info.md).

Each family now points at its googlefonts repository, where the work was merged today:

* Krona One, Ovo, Pompiere, Short Stack, Sonsie One: METADATA.pb named googlefontdirectory-hg; their googlefonts repositories hold the same FontLab .vfb and FontForge .sfd files, and the .sfd files are imports of the shipped fonts. So the shipped fonts were converted to .glyphs with babelfont-rs's TTF reader (googlefonts/kronaone#1, ovo#1, pompiere#1, shortstack#1, sonsieone#1).
* Beth Ellen: its .sfd at d6c8d9b, the revision Google Fonts ships, converted to .glyphs after one documented edit (UnderlinePosition, so the build gets the release's -249). Three later commits on its main branch stay in history but are not part of the conversion (googlefonts/BethEllen#1).

Every build was rebuilt from the recorded commit and checked against the shipped fonts with https://github.com/felipesanches/gf-source-modernization (table gate and functional gate, hinting included). Pompiere has one known difference, disclosed in its upstream_info.md and README: the font has no GPOS, so the shaper places combining marks from glyph bounding boxes; 174 of the release's are stale while a compiled font's are exact, so 25,596 of 26,656 base+mark pairs place the mark differently, by up to 35 units of 2048. The other five have none.

Assisted by an AI agent (Claude Opus 5.5)
