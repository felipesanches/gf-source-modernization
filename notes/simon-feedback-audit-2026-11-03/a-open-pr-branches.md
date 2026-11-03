# Audit A: the open babelfont PR branches and the two new ones (2026-11-03)

Read-only review of each branch's net merge with babelfont main a93e1325 against Simon's principles
(README.md here). Spot-checked by the main session: 26fdcfa9 changes only ID 1 (ID 16 is not in
LOCALIZED_PROPERTY_NAME_IDS, so #117 already writes its localizations as entries); #111's
KEY_EXPLICIT_ANCHORS "babelfont.explicitAnchors" (font.rs:126) has no Glyphs ingress; #119 writes
isFixedPitch (customparameters.rs:363) with no ingress; #109's "sfd.lcaret" marker (fontforge.rs:2101,
emit.rs:1063); #121's ufo2ft featureWriters key (features.rs:9).

| PR         | severity | main issue                                                                                     | right shape                                                   |
|------------|----------|------------------------------------------------------------------------------------------------|---------------------------------------------------------------|
| #104       | BLOCKER  | P12: explicit GDEF GlyphClassDef prefix (fontforge.rs:4034/4081); drops names FEA cannot spell; a second mark rule beside main's infer_mark_categories_from_anchors | reader sets glyph.category with FontForge's automatic rule (mark = first non-cursive anchor is a mark, ligature = Ligature2 result, base otherwise); what the compiler still re-infers -> documented source edit |
| #105       | NIT      | text: 105.md pastes the superseded reply before the follow-up; two-lookup pair keeps the later value (OpenType sums) | as is; post one line answering Simon + the follow-up        |
| #106       | NIT      | P3 risk: stated OS/2 version kept in format_specific                                           | as is; or custom_ot_values.os2_version later                  |
| #108       | FIX      | heuristic placement after the marker, not the SFD's lookup order; P1 (fontforge.rs:2677); P10 + contradiction with #121 | drop if #121 lands in any form; else follow the SFD lookup order |
| #109       | FIX      | P2/P11: sfd.lcaret marker; SFD writer drops carets instead of writing LCarets2; RTL by Unicode range misses unencoded ligatures | reader -> caret_N anchors only; SFD writer caret_N -> LCarets2 |
| #110       | NIT      | P1 comments (fontforge.rs:2087, setsubcategory.rs:34); duplicated logic                       | as is, comment = the rule only                                |
| #111       | FIX      | P11 smuggled key, P2 no ingress of Propagate Anchors                                           | model field (Font.propagate_anchors) + Glyphs read/write; SFD reader sets false |
| #112       | NIT      | P1 test comment                                                                                | as is                                                         |
| #117       | FIX      | P2: no ingress of Name Table Entry (as #101); P1 NIT (customparameters.rs:578); P10 vs typographic-family-names | add interpret_name_table_entries (covers #101 too)       |
| #119       | FIX      | P2: isFixedPitch export without ingress (the #90 complaint); P10 monospace.rs shared with #120 | add the Glyphs ingress; the generic filter is fine           |
| #120       | NIT      | text: 120.md pastes three replies; P10 overlap with #119 (identical file)                      | as is; post the apology line + the rework paragraph          |
| #121       | BLOCKER  | P11: reader plants ufo2ft featureWriters in Glyphs userData and norad lib (fontforge.rs:2786, features.rs:9-13); P4/P5: babelfont's fontir honours it; new keys babelfont.anchor_lookups, sfd.class; AddMaster text-matches lookup lines; keeps '# Automatic Code' while disabling its writers; second fea_can_name | (a) the Thabit problem is a category problem: #104 reworked to categories, drop the explicit lookups, exact lookups as a font-repo source edit; or (b) lookups in their feature blocks without the marker, flagged PossiblyAutomaticCode.automatic, AddMaster drops automatic code, no featureWriters, no fontir change |
| typo-names | FIX      | P2/P3: writer maps typographic_family -> familyName, reader still maps familyName -> family_name (glyphs3.rs:286, :591); P10 vs #117 | Glyphs reader maps familyName(s) -> typographic_family and derives ID 1; rebase on #117 once merged |
| family-ids | FIX      | message/body say IDs 1 and 16, the commit changes ID 1 only; with typo-names ID 16 localizations go out twice (familyNames and entries); premise contradicts 3c532e9e | open only after #117 + typo-names merge, one commit, corrected text; decide one mechanism for ID 16 |
| #114, #116 | CLOSE OK | P9 class (c)                                                                                   | documented source edits (3 repos; Comic Relief)              |

Also (commits on the PR branches of https://github.com/felipesanches/babelfont-rs branches): several branches keep an "add a FontForge flag" commit followed by its replacement (#104 0b5f38e0 ->
"fontforge: write the SFD's glyph classes as GDEF GlyphClassDef"; #106 987264fd -> "fontforge: drop fsSelection bits a stated OS/2 version 1-3 lacks"; #111 12a5fc18 -> "fontforge: state that SFD anchors are explicit"; #119 604c3294 + "Move the one-width rule back into the OS/2 defaults filter (#119)" cancel; #120
1fe9fc9d + "Move the one-width rule back into the OS/2 defaults filter (#120)" cancel; #121 24c239bd -> "fontforge: write the anchor lookups the SFD states"; typo-names 1fafc24a fixes 623fb9c3). Squashing
needs a force push (Felipe's decision; our rule is no force push, so they stay and the PR bodies say so).

Textual conflicts between our PRs (merge-tree with merge base a93e1325): fontforge.rs #104x#109, #104x#110,
#104x#111, #105x#106, #105x#121, #106x#121, #108x#121, #109x#110; tests.rs #104x#105, #104x#111, #105x#111,
#108x#109, #108x#110, #108x typo-names, #109x#110, #109x typo-names, #110x typo-names (mostly appends at the
end of the file); customparameters.rs #111x#119, #117x typo-names. 17 pairs.

Overlaps in meaning: #104, #110, #121 and main's infer_mark_categories_from_anchors all decide mark/base;
#108 reorders around a marker #121 switches off; #111 and #121 both work around the compiler's anchor
handling; fea_can_name twice (#104, #121); ID 16 localizations twice (#117 + typo-names).

Caveat: the API rate limit stopped this reviewer from reading the live threads of #106-#121; Simon's
comments on them are in tools/probes/open_prs/results-2026-11-03-babelfont-comments.txt.
