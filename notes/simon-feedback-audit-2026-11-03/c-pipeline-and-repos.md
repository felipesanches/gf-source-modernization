# Audit C: the pipeline and the font repositories (2026-11-03)

Read-only review of tools/recipe.py, tools/land.py, tools/workarounds.py, plans/*.json, the landed repos
(sfd-reland-repos, 165 excluding .prev; vfb-reland-repos-fixes) and the roadmap texts against Simon's
principles (README.md here). Spot-checked by the main session: fontc 22388c88 ("Apply the static
instance's metadata to static Glyphs builds", Cosimo Lupo, 2026-10-15) is on fontc main and in no tag;
in carlito (the convert commit), sansation (the convert commit) and jomolhari (the convert commit) the GlyphClassDef enters inside the
convert commit.

## Q1. Filters the recipe passes

| flag                                  | upstream          | FF/FL-specific         | families                       | sev |
|---------------------------------------|-------------------|------------------------|--------------------------------|-----|
| --fontforge-os2-defaults              | yes (#91)         | yes, exporter defaults | all 101 SFD repos              | NIT |
| --fontforge-underline-position        | yes (#91)         | yes, exporter offset   | 101 SFD                        | NIT |
| --fontforge-height-glyph-count-mean   | yes (#91)         | yes, pre-2012 build    | 85 SFD                         | NIT |
| --add-instance-per-master             | yes               | no                     | all SFD + VFB                  | OK  |
| --infer-mark-category                 | yes               | no                     | 101 SFD                        | OK  |
| --set-subcategory                     | yes               | no                     | 101 SFD                        | OK  |
| --keep-source-advances                | yes (#97)         | no                     | 101 SFD + all VFB              | OK  |
| --round-coordinates                   | yes (#100)        | no                     | 57 SFD + VFB                   | OK  |
| --correct-path-direction              | yes               | no                     | 65 SFD, 229 VFB styles         | OK  |
| --correct-conjunct-category           | yes               | no                     | lohitbengali, lohittamil       | OK  |
| --add-notdef                          | no (#120)         | no (reworked)          | 0 landed; tuffy R/I + ~7 wait  | FIX |
| --infer-fixed-pitch                   | no (#119)         | no (reworked)          | NovaMono                       | NIT |
| --glyph-order-and-alias-db            | no ("Add a filter for the GlyphOrderAndAliasDB Unicode column")     | no (AFDKO GOADB)       | 30 VFB styles (Mukta etc.)     | FIX |

The three upstream --fontforge-* filters predate the 2026-10-02 rule (merged in #91): add no more of the
kind; Tuffy states the same OS/2 values as setfield source edits, so one quirk is handled two ways.
land.py:599,611 silently drops a flag the converter does not know (FIX: fail instead).

Post-conversion edits written by land.py/workarounds.py:

| edit                                        | repos                          | principle        | sev | shape                                                     |
|---------------------------------------------|--------------------------------|------------------|-----|-----------------------------------------------------------|
| table OS/2 { WeightClass/WidthClass } FEA   | 44 SFD/binary + 23 VFB         | P12, P5          | FIX | drop once gftools-rust pins a fontc with 22388c88          |
| gdef_classes_fea (GlyphClassDef prefix)     | carlito, sansation, jomolhari  | P12, layering    | FIX | its own documented source-edit commit after the conversion |
| isFixedPitch custom parameter               | nanumgothiccoding              | P3               | NIT | TTF reader reads post.isFixedPitch (#119's model field)    |
| italic-angle metric rewrite                 | SFDs with fractional angle     | P3               | NIT | model keeps the real angle                                 |

## Q2. Dependencies on rejected or under-review behaviour

- BLOCKER #104 (categories only, bottleneck 3c): 16 families wait on it -- kottaone, macondo, monoton,
  oleoscript, oleoscriptswashcaps, poly, ruluko, salsa, smythe, titanone, unifrakturcook (#104 alone);
  patrickhand, lustria (+#106); passionone, comicrelief, tuffy (+#117 + typographic-family-names).
  recipe.py:147-150 assumes the #104/#106/#111/#121 reader behaviour. The setglyphclass edits (miama,
  tuffy, ultra) do not depend on #104 (main reads GlyphClass:, fontforge.rs:1668).
- BLOCKER #121: featureWriters lib keys (P11, P4), mark/mkmk/curs as FEA (P12), sfd.* anchor keys. Its
  motivating case (Thabit's 82 unclassed Arabic bases) is a class problem -> categories-only #104.
  Affected: thabit, cardo, and #108.
- FIX #111: model field + symmetric Glyphs mapping (thabit, cardo).
- OK: #105 (P7; italiana, sanchez); #106; #114/#116 cases already became documented edits (corben,
  limelight, mountainsofchristmas, nothingyoucouldo, puritan, unifraktur, comicrelief).
- NIT: Thabit's truncateanchors edit (600+ anchors for one-unit differences): P6 suggests disclosure.
- FIX: vfb-export-rules (audit B).
- NIT: almarai and dongle cite "a local integration build" (neither upstream nor sanctioned) and carry the reverted prefix
  47f99442; both WITHDRAWN, re-land before any revival.
- FIX P10: 20 of the 91 pairs among the 14 local branches conflict (the open_prs probe tests each only
  against main).

## Q3. Feature code in the landed repos

- GlyphClassDef: 5 repos -- carlito, sansation, jomolhari (gdef_classes_fea; legitimate as a source
  statement because no category expresses those classes, tools/probes/gdef_prefix_ab, but inside the
  convert commit, FIX before pushing); almarai, dongle (reverted reader; withdrawn).
- Mark lookups as FEA: 4 binary conversions (alef, almarai, dongle, lato) that also carry anchors: Simon's
  own TTF reader emits the remaining GPOS as FEA (c4640847, c282cf2c). NIT.
- Kerning as FEA: 17 repos. 14 binary conversions with no master kerning, 10 already published (comingsoon,
  jua, oranienbaum, portersansblock, ptsans, ptsanscaption, ptsansnarrow, ptserif, ptserifcaption,
  rocksalt); italiana, sanchez wait on #105; cardo residual. P7: the TTF reader should turn PairPos into
  master kerning (an upstream reader change). FIX, not blocking.
- OS/2 WeightClass FEA: 44 + 23 VFB repos (Q1).

## Q4. gftools-rust and glyphslib-rs

- static-autohint (branch head): OK; autohintTTF/ttfaUseScript match Python gftools (schema.py:123,128;
  googlefonts.py:47,49,517-525).
- instantiate-keep-instance (branch head): FIX text -- "fontc does not read a single-master source's instance
  weightClass yet" is true of fontc 1.0.0 only; main reads it since 22388c88.
- fix-v2-master-name-omitted-weight (branch head): OK.
- Config keys emitted (recipe.py:103-117): productionNames, reverseOutlineDirection,
  decomposeTransformedComponents, flattenComponents valid in both builders; autohintTTF ignored by Rust
  until static-autohint; flattenComponents default differs (Rust false, Python true), harmless here.

## Q5. Texts premised on rejected changes

bottleneck.md item 3 (#121 push + reply), 98-99 ("all 13 ... CLEAN; 21 need only night C's #104 #106 #105"),
107-112 (vfb-export-rules as exporter rules in the reader), 136-138 ("convert without anchors" deletes
source data: drop); 23-roadmap-modern-sources.tex:250-253 (S4 assumes all PRs merge) and :334 ("Issues to
file: static weight class" -- fixed on fontc main; 22-fontc-problems.tex:150-157 stale the same way);
PLAN-2026-10-01-followup.md:24,31,33,38,69 (rejected shapes; superseded by the 2026-10-02 decision);
recipe.py:147-150.
