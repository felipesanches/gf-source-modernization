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
2. Its flag is IgnoreMarks, or 0 in a font where no glyph is a mark (then the two read the same):
   with GDEF glyph classes, none in class 3; without them, no glyph whose codepoint a shaper takes
   for a mark (general category Mn, Mc or Me, not default-ignorable). Otherwise the font keeps its
   kerning as feature code. (Corrected 2026-11-03: the first version looked only at the categories
   the reader assigns, which are all bases in a font without GDEF that attaches no marks; Forum
   failed shaping in the acceptance run, see marks.py below.)
3. No `kern` lookup is registered for a right-to-left script (none is today; a later change can add
   it).
4. Precedence as a shaper applies it: within one lookup, the first subtable holding a pair wins
   (format 1 before the class pairs of a later subtable); across lookups, the values add.
5. Format 2 class pairs become first/second kern groups (Simon's model already has them), named after
   their first glyph; class 0 of the second class definition is "every glyph not in a class" and is
   expanded only where the pair has a value.

Measured further (groups.py, groups-2026-11-03.tsv, and the lookup/subtable order of the 166): the
model keeps a glyph in at most one first-side and one second-side group (the Glyphs rule), and a glyph
pair overrides its group's value. 162 of the 166 styles' class definitions fit one group per side (42 have
no class pairs at all); the 4 that do not are Carlito's. 161 of the 162 have a single `kern` lookup whose
glyph-pair subtables all come before its class subtables -- exactly the model's "a glyph pair overrides
its group". So the conditions, all required, become:

6. One `kern` lookup, its format 1 subtables before its format 2 ones (161 styles meet 1-6).
7. Each glyph in one class per side across its format 2 subtables (the class becomes `@<first glyph>`
   in first_kern_groups / second_kern_groups); otherwise keep the feature code.

Everything else stays exactly as today (feature code), so the change can only move kerning that the
model expresses: 161 of the 281 styles move, 120 keep what they have (110 have no GPOS kerning).

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

## Marks in flag-0 fonts without GDEF (marks.py, marks-2026-11-03.tsv)

The acceptance run's first regression was Forum: no GDEF, a flag-0 `kern` lookup, U+0300..U+030C
encoded; 7195 of 8300 kern+mark runs differed, because master kerning compiles to a lookup that ignores
marks and a shaper without glyph classes takes U+0301 for one. marks.py lists every flag-0 style:
48 with no GDEF and no marks and 45 with GDEF classes and no marks are SAFE; 65 without GDEF and 4 with
GDEF (Carlito) have marks and keep their feature code under the corrected rule 2.

The functional gate missed most of the 65: its kern+mark corpus put only U+0301, U+0308 and U+0323
between a kerned pair, and most of these fonts encode other marks (U+0312, U+0315, U+0326,
dotaccentcmb). In the acceptance run 32 repositories with marks moved their kerning and passed (exactly
the RISK rows of kern_marks_risk.py), and the 6 encoding U+0301 failed (Forum, PT Sans, PT Sans
Caption, PT Sans Narrow, PT Serif, PT Serif Caption). Gate gap G, fixed in functional_gate.py: the
corpus also puts up to KERN_MARKS (8) of the marks the two fonts share between a kerned pair.

kern_marks_risk.py asks the same of every landed CLEAN repository on every route: the only release
kern lookups without IgnoreMarks whose marks the old corpus never tried are those 32, and all of their
current landings keep the kerning as feature code (flag 0 kept). No published landing is affected.

    python3 -I tools/probes/ttf_gpos_kerning/kern_marks_risk.py > tools/probes/ttf_gpos_kerning/kern-marks-risk-2026-11-03.tsv

## Other positioning features (Share)

The run's other regression was Share: GPOS registers cpsp and kern for latn alone, and a shaper falls
back to latn for a run of another script. Master kerning has no script; the compiled font registers
kern for DFLT and grek too, where cpsp is then missing: 67 of 6120 cpsp runs differed (U+2126,
U+2206 and other non-Latin codepoints lose cpsp). So a further condition, all required:

8. GPOS has no feature besides `kern`, and every language system registers it. Of the 66 repositories
   that moved kerning, 5 had other GPOS features (Alfa Slab One, Dongle, Libre Caslon Display, Share,
   Titillium Web); they keep the feature code. No language system without `kern` exists today.

    python3 -I tools/probes/ttf_gpos_kerning/marks.py tools/probes/ttf_gpos_kerning/census-2026-11-03.tsv > tools/probes/ttf_gpos_kerning/marks-2026-11-03.tsv

## Acceptance run 1 (accept-2026-11-03-run1.txt)

accept.sh over the 183 repositories with the first version of the reader change (rules 1-7 with the
old rule 2): 176 kept their verdict, 7 lost CLEAN (Forum and the five PT families: marks; Share: cpsp).
The run's verdicts carry -UNCOMMITTED-EVIDENCE from nanumbrushscript on, because these probes were
being written in the evidence tree meanwhile; the results are not affected. Run 2 re-lands with the
corrected rules 2 and 8.

## Acceptance run 2 (run2-repos.txt)

The 72 binary-route repositories that rules 2 and 8 or gate gap G can change: a shipped style encodes
a mark (Mn, Mc, Me, not default-ignorable), or GPOS has a feature besides `kern`. The rest of the 183
read the same under the corrected rules and are not re-landed.

    BF_TREE=<branch 2026-11-02 + the kerning commit> REPOS=tools/probes/ttf_gpos_kerning/run2-repos.txt sh tools/probes/ttf_gpos_kerning/accept.sh <scratch dir>

Result (accept-2026-11-04-run2.txt; converter babelfont branch 2026-11-02 + the corrected kerning
commit): 62 of the 72 keep their verdict, among them the 7 run 1 lost (Forum, the five PT families and
Share are CLEAN again, their kerning feature code kept). The other 10 are the IM Fell families,
CLEAN-DISCLOSED -> RESIDUAL, and the kerning change is not why: they have no GPOS kerning, and their
converted sources equal their current landings except for random master ids. Gate gap G now puts
U+0326 between kerned pairs, and IM Fell's disclosed U+0326 defect (bottleneck 9: commaaccent at x=279
in the release, 480 in the build; base+mark already 249 of 253) shows there too: kern+mark 3778 of 3916
in IM Fell English Roman. Their accepted list needs that line when they are re-landed (land.py
--write-accepted), once Felipe decides bottleneck 9.

So the change passes the design's bar: no style loses CLEAN through the reader, and no shaping run
differs because of it.

Moved: 79 of the 166 SIMPLE styles (61 families) carry master kerning after runs 1 and 2 (the .glyphs
of run 2 for its 72 repositories, of run 1 for the rest); the other 87 keep the feature code (69
flag-0 styles with marks, the other-GPOS-feature families, and the census exclusions of rules 6-7).
