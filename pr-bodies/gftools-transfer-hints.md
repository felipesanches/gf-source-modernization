Title: builder: transfer a font's own TrueType hinting (gftools transfer-hints)

Body:

A source format cannot carry a compiled font's TrueType hinting: its programs address the glyphs' points by index. So a font rebuilt from sources currently loses the hinting its release had.

This PR adds `gftools transfer-hints SRC DST`. SRC is the hinted font, or a `.ttx` dump of one (so a source repository can keep it as text); DST is the font built from sources.

- The hinting tables are copied whole: gasp, fpgm, prep, cvt, the maxp limits, head flags 2 to 4, hdmx, LTSH, VDMX.
- Each glyph that draws SRC's outline takes SRC's points, recorded box, side bearing and program. The same outline allows another start point, missing on-curve points halfway between two off-curves, repeated points, one-point contours and a horizontal shift, which compilers produce; a composite needs the same components.
- An instructed glyph that does not match is refused with its reason, and nothing is written.

The `transferHints` builder operation runs it on each font named in the new `hintingFiles` config key, in place of autohinting.

Test: on 29 fonts of 19 Google Fonts repositories built with fontc, all keep the release's hinting (hinted rendering identical at 8 to 24 ppem). Four unit tests.

Assisted by an AI agent (Claude Opus 5.5)
