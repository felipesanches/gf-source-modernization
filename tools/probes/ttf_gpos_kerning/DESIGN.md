# TTF reader: GPOS pair kerning into the master kerning (P7)

Why: Simon on babelfont#105, "it would be better if we put kerning into the master kerning, not into
FEA". The TTF reader (his, #131) uncompiles every GPOS lookup to feature code through sr-aef, so the
families converted from their binaries keep their kerning as feature code (14 landed, 10 of them
published: comingsoon, jua, oranienbaum, portersansblock, ptsans, ptsanscaption, ptsansnarrow, ptserif,
ptserifcaption, rocksalt).

## What the binaries need (census.py, census-2026-11-03.tsv, the 281 styles of families-binary.tsv)

| kern feature in GPOS                                                                                  | styles |
|-------------------------------------------------------------------------------------------------------|--------|
| none                                                                                                  | 110    |
| SIMPLE: pair lookups only, first glyph's XAdvance only, flags 0 or IgnoreMarks, no contextual caller  | 166    |
| COMPLEX: value records beyond XAdvance, or flags RightToLeft/IgnoreBaseGlyphs (almarai x4, jomolhari) | 5      |

Of the 166: PairPos format 1 and 2 together in 124, format 1 only in 43, format 2 only in 4; flag 0 in
161, IgnoreMarks in 5; none registered for arab or hebr.

## The rule (a reader change, no flag: P9)

The reader moves a font's `kern` lookups into the default master's kerning, and leaves them out of the
uncompiled features, only when every lookup the `kern` feature uses is SIMPLE and the lookup flag
cannot change what the kerning model means:

1. Every `kern` lookup is type 2 (or an extension of type 2), ValueFormat1 is XAdvance alone and
   ValueFormat2 is 0, and no contextual lookup calls it.
2. Its flag is IgnoreMarks, or 0 in a font whose GDEF classes no glyph as a mark (then the two read
   the same). Otherwise the font keeps its kerning as feature code.
3. No `kern` lookup is registered for a right-to-left script (none is today; a later change can add
   it).
4. Precedence as a shaper applies it: within one lookup, the first subtable holding a pair wins
   (format 1 before the class pairs of a later subtable); across lookups, the values add.
5. Format 2 class pairs become first/second kern groups (Simon's model already has them), named after
   their first glyph; class 0 of the second class definition is "every glyph not in a class" and is
   expanded only where the pair has a value.

Everything else stays exactly as today (feature code), so the change can only move kerning that the
model expresses.

## Acceptance

- Unit tests in ttf.rs beside test_legacy_kerning: format 1, format 2 with groups, first-subtable
  precedence, two lookups adding, a flag-0 font with marks keeping its feature code, a COMPLEX lookup
  keeping it.
- Re-land every families-binary.tsv repository with the change (tools/land.py, one job at a time) and
  compare with the current landings: no style may lose CLEAN, and no shaping run may differ
  (tools/functional_gate.py); the census's 166 styles should carry master kerning and no `kern`
  feature code.
- Then: the PR to simoncozens/babelfont-rs (problem first, P1/P15 comments), and for the 10 published
  repositories a new commit each (no force push) once it is merged and released in the pinned
  converter.
