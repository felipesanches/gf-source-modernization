# Audit B: the unproposed VFB babelfont branches (2026-11-03)

Read-only review of local branches against Simon's principles (README.md here), babelfont main a93e1325.
Line numbers: babelfont/src/convertors/vfb.rs at "Carry the weight and width classes on the instance". Spot-checked by the main session: the
duplicate `icu_properties` key (merged Cargo.toml lines 102 and 106) and the reader's Glyphs custom
parameters (vfb.rs l.120 set_custom_parameter, l.419/425/441/764, l.778 KEY_WEIGHT_CLASS) are real.

## Topology

vfb-names, vfb-truetype-info-2026-10-29, vfb-kerning-2026-10-29, vfb-filters-2026-10-29 and
infer-mark-category-encoded-2026-10-29 fork from b24ffd03 (8 behind a93e1325).
vfb-integration-2026-10-29 = vfb-export-rules-2026-10-29 ("Carry the weight and width classes on the instance") merges all five plus 5 export-rule
commits. fix-glyphs3-path-start sits alone on 91bf8bb5.

## Cross-cutting

- P11 BLOCKER: the VFB reader writes Glyphs custom parameters into format_specific (l.120, via
  glyphs3::KEY_CUSTOM_PARAMETERS) and KEY_WEIGHT_CLASS/KEY_WIDTH_CLASS on the instance (l.778). The model
  has custom_ot_values.{os2_fs_type, os2_panose, os2_vendor_id: Tag, os2_us_weight_class,
  os2_us_width_class, head_lowest_rec_ppem} and MetricType::{Strikeout*, Sub/Superscript*,
  UnderlinePosition}; the FontForge reader uses them and glyphs3 exports them. fs_type_bits (l.136)
  duplicates upstream.
- Stale: "values written into the metrics array are silently ignored" (l.117, l.417, "Read the VFB TrueType and OS/2 block") is false
  since #90 (0b559476).
- P1: comments full of fontc/fontmake/makeotf/fontspector/Google Fonts detail and corpus counts
  (l.30, 58-65, 78, 91, 117, 134, 417, 750, 797, 813, 901-902, 924-937).
- P10: vfb-names x vfb-truetype-info, vfb-names x vfb-kerning, vfb-truetype-info x vfb-kerning conflict
  in vfb.rs; must go as a stack, each rebased on the previous.
- Anonymous tuples: parse_gdef_anchors -> Vec<(SmolStr, i32, i32)> (l.233), parse_class_flags (l.194),
  pending_kerning (l.342), pending_classes (l.347), read_pairs in the GOADB filter.
- P5: decoding raw VFB records (PostScript Info, Kerning Class Flags, Glyph GDEF Data) belongs in
  vfbreader (jenskutilek/vfbLib-rust), which exposes them as RawData; in babelfont only as a stated stopgap.

## Per branch

| branch                      | verdict               | what to do                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
|-----------------------------|-----------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| fix-glyphs3-path-start      | ready after rebase    | rebase on a93e1325; the TTF reader (#131, ttf.rs:931) calls path.reverse(), so TTF conversions' start points change -- say so; the 27 published binary repos would churn on re-conversion                                                                                                                                                                                                                                                                                                       |
| infer-mark-category-encoded | BLOCKER (build break) | duplicate icu_properties key after merge; make the existing dep non-optional or gate the filter; body: "via fontbe" stale, "all mark-side" should be "any `_` anchor". Separately: the reader parses the VFB GDEF glyph class and drops it (`_glyph_class`, l.235); by P12 set glyph.category from it                                                                                                                                                                                           |
| vfb-names                   | ready                 | base of the VFB stack (NIT: family fallback is the PostScript name)                                                                                                                                                                                                                                                                                                                                                                                                                             |
| vfb-kerning                 | FIX                   | native kerning/groups/anchors (P7, P11 ok); tuples, P1 (l.813); "vfb: drop feature-code references to glyphs absent from the font" hides SubsetLayout in the reader (l.909) with an unverified fontmake claim: use the generic subsetlayout filter run by the pipeline, or a .fea source edit; "vfb: carry hhea line gap into master metrics" (line gap) ready                                                                                                                                                                                                                                  |
| vfb-truetype-info           | BLOCKER (P11, P4)     | "Read the VFB TrueType and OS/2 block" OS/2 block: valid import, rewrite to custom_ot_values/metrics; "Only emit a vendor ID that is a legal OpenType tag" vendor ID -> os2_vendor_id; "Fix VFB version strings and multi-line name records": "Version " prefix breaks P3 (leave name ID 5 to the compiler), single_line duplicates singlelinenames: drop; "Do not put a copyright notice in the description name record" duplicates dropcopyrightdescription: drop; "Keep head.fontRevision in step with the version name record" fontRevision from string: P3, our probe contradicts it (97/194 vs 93/192): drop, source edit; "Keep VFB glyph names instead of production names" "Don't use Production Names" (l.807): P4/P5, drop, use noProductionNames in config.yaml |
| vfb-export-rules            | BLOCKER (P11, rule c) | per rule below; body inaccurate (title frames all as exporter rules, hides the 15-commit dependency, cites unpublished an unpublished evidence revision)                                                                                                                                                                                                                                                                                                                                                                 |
| vfb-filters                 | FIX / mostly drop     | "Add a filter to take the version from the feature file" versionfromfeatures: P6/(c), 6 families -> documented version edits; "Add a filter for the GlyphOrderAndAliasDB Unicode column" glyphorderandaliasdb: acceptable generic filter, fix P1 prose, explicit path, named tuple                                                                                                                                                                                                                                                                                                                |

## The five export rules

| rule               | does the .vfb store it?                                | class        | shape                                                                                    |
|--------------------|--------------------------------------------------------|--------------|------------------------------------------------------------------------------------------|
| underline top      | yes (Type 1 centre-line value)                         | (a) import   | reader writes MetricType::UnderlinePosition (pos + thick/2); doc the post semantics      |
| PANOSE entry       | yes, two copies; the font-level panose is the real one | (a) import   | custom_ot_values.os2_panose                                                              |
| x / cap height     | yes, last two fields of PostScript Info                | (a) import   | reader writes model metrics; decoder belongs in vfbreader                                |
| hhea from typo     | stores its own hhea, which the commit overwrites       | (c) exporter | drop "Write hhea's vertical metrics from the OS/2 typo values" (l.970); documented hhea edit per font repo (178/157 not unanimous)        |
| weight/width class | yes (weight_code, TrueType block width)                | (a) import   | custom_ot_values.os2_us_{weight,width}_class; addinstancepermaster, not KEY_WEIGHT_CLASS |

## Order

1 fix-glyphs3-path-start; 2 infer-mark-category-encoded (after the Cargo fix); 3 vfb-names; 4 vfb-kerning
(on 3); 5 vfb-truetype-info (reworked, on 4); 6 export rules (reworked: four reader rules folded into 5's
series, hhea to font repos); 7 vfb-filters (optional). Drop from babelfont: "Keep VFB glyph names instead of production names", "Do not put a copyright notice in the description name record", single_line
of "Fix VFB version strings and multi-line name records", "Keep head.fontRevision in step with the version name record", "Write hhea's vertical metrics from the OS/2 typo values", the KEY_WEIGHT_CLASS instance, the reader's own subsetting ("vfb: drop feature-code references to glyphs absent from the font").
