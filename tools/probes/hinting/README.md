# Hinting probes

Question (google/fonts#11237, comment 6650283300): can the modernized repositories keep the TrueType hinting that google/fonts ships, instead of losing it?

| script            | question it answers                                                                                                                    | command                                                                                                                     |
|-------------------|----------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------|
| `census.py`       | Which kind of hinting does each shipped font carry?                                                                                    | `$PY -I tools/probes/hinting/census.py families.tsv families-next.tsv families-binary.tsv families-vfb.tsv`                 |
| `points.py`       | Would the release's glyph programs address the same points in our build?                                                               | `$PY -I tools/probes/hinting/points.py <shipped.ttf> <built.ttf>`                                                           |
| `run_points.sh`   | `points.py` over freshly built landed repositories (published gftools-rust 1e638bd)                                                    | `tools/probes/hinting/run_points.sh <scratch> <repo>... > points.txt`                                                       |
| `roundtrip.py`    | Does a release's hinting come back exactly through ufo2ft libs, or through a separate hinting file applied after compiling?            | `$PY -I tools/probes/hinting/roundtrip.py <scratch> <release.ttf>... > roundtrip.txt`                                       |
| `hinting_file.py` | Prototype of the route (a) builder operation: extract a release's hinting to text; apply it to a compiled font                         | `$PY -I tools/probes/hinting/hinting_file.py extract <release.ttf> > X.hinting.json`; `... apply X.hinting.json <in> <out>` |
| `midpoints.py`    | How many instructed glyphs have explicit on-curve points fontc would drop?                                                             | `$PY -I tools/probes/hinting/midpoints.py census.tsv <google/fonts> > midpoints.txt`                                        |
| `e2e.py`          | Route (a) end to end: release -> babelfont -> .glyphs -> fontmake / fontc -> hinting file -> gate; which step still loses the hinting? | `$PY -I tools/probes/hinting/e2e.py <babelfont> <gftools-builder> <scratch> <release.ttf>... > e2e.txt`                     |
| `predict.py`      | What will functional_gate's hinting check say about each repository, unbuilt?                                                          | `$PY -I tools/probes/hinting/predict.py census.tsv published.txt > prediction.tsv`                                          |
| `check_built.py`  | Does the hinting check agree with `predict.py` on fonts actually built?                                                                | `$PY -I tools/probes/hinting/check_built.py prediction.tsv <shipped> <built>...`                                            |

`$PY` is a Python with fontTools (the `PY` of the repository README). Shipped fonts were read from a google/fonts clone at 2eb0b48d5; the METADATA PRs since then change no font binary.

## Results (2026-11-05)

`census-2026-11-05.tsv`: 477 shipped fonts of the 300 repositories in the four family tables.

| class         | meaning                                                               | fonts | repos |
|---------------|-----------------------------------------------------------------------|-------|-------|
| other         | glyph programs from another hinter (FontLab, VTT, FontForge, by hand) | 173   | 102   |
| ttfautohint   | name ID 5 records ttfautohint and its options (v0.8 to v1.6)          | 57    | 25    |
| no-glyph-code | a prep (sometimes an fpgm no glyph calls), no glyph instructions      | 195   | 158   |
| none          | no fpgm, prep or glyph programs                                       | 52    | 22    |

A repository with several fonts can be in more than one class.

The no-glyph-code class is the setup of fontspector's `smart_dropout` check (fontbakery#4829) for unhinted fonts: 190 of its 195 fonts have a prep that is exactly B8 01 FF 85 B0 04 8D (PUSHW 511 SCANCTRL PUSHB 4 SCANTYPE: smart dropout control), what `gftools fix-nonhinting` writes, with gasp 65535:15 in 162 of them. Our builds keep it: all 18 fonts built for `points-2026-11-05.txt` have exactly that prep, gasp 65535:15 and no fpgm (gftools-rust `fix`). What differs in that class: 83 fonts also carry an fpgm that nothing calls (no effect on rendering), and 28 have another gasp (16 of them 8:2,16:1,65535:3, 5 none). The 52 fonts of class none have no prep; our builds add that same one.

Our builds carry no hinting at all: gftools-rust 1e638bd's single-master static recipe is `fontc` then `fix`, with no autohint step (`build_a_static` in `gftools-builder/src/recipe_providers/googlefonts.rs`; only `instantiate_a_static` autohints). Checked on the Actor and Stalinist One builds: no fpgm, no glyph instructions, name ID 5 `Version ...;fontc 1.0.0`. The upstream_info.md text "the build is hinted by ttfautohint" holds for Python gftools-builder, not for the builder those texts name.

`points-2026-11-05.txt`: 8 repositories, 18 fonts. 2981 of 5478 glyphs are point-identical; 2496 differ, 2490 of them instructed in the release (of 5318 instructed glyphs). Where the points are lost, on Actor `O` (release: 20 + 16 points, on-curves at (51,341), (380,691), (709,340) among them): the .glyphs source written by babelfont 26fdcfa stores every implied on-curve point as an explicit `q` node (32 + 24 nodes, fractional midpoints such as (81.5,173)), so it no longer records which on-curves the release had; it lists the contour from (51,438,o), and Glyphs takes the last node as the start; fontc 1.0.0 then drops every on-curve at the exact midpoint of two off-curves, the release's own (380,691) included, and outputs 18 + 16 points. Cantora One `B` keeps its point count and is rotated by two. Stalinist One is the exception: 336 of 337 identical. A glyph program addresses points by index, so copying the release's instructions onto these builds would hint wrong points in about half of the instructed glyphs.

## The gate (2026-11-05)

Hinting is now the eighth check of `tools/functional_gate.py` (its docstring states the rules), so land.py, verify_landed.py (and through it push.sh) and verify_metadata.py `--build` all refuse a conversion whose hinting differs from the release's, unless the plan's `accepted` list states the difference (ALLOW_DISCLOSED=1). `tools/probes/functional_gate/MUTATIONS.txt`: 17 of 17 mutations fail exactly their expected checks, 8 of them hinting cases.

`prediction-2026-11-05.tsv` (published = the 176 repositories of `logs/metadata-audit-2026-11-04/main-after-11237.md`): our builds all carry the smart_dropout prep, gasp 65535:15, no fpgm and no glyph programs. The gate accepts what fontspector asks for (Felipe, 2026-11-05): googlefonts/gasp fails a missing gasp and warns on any gasp other than 65535:15, and its hotfix (gftools fix_unhinted_font) writes that gasp with the smart_dropout prep. So a build may state gasp 65535:15 in place of any other, and the smart_dropout prep where the release has none; nothing else (smart_dropout itself skips a font without prep). A font therefore passes unless its release is instructed. The census does not disassemble: 5 releases without glyph programs have a prep other than the smart_dropout setup (Allerta Stencil, East Sea Dokdo, Black And White Picture, Audiowide, Freckle Face), and each of those CALLs its font program, so they count as instructed.

| repositories | pass | fail: release instructed |
|--------------|------|--------------------------|
| published    | 89   | 87                       |
| not yet      | 79   | 45                       |

Before the fontspector rule the same census failed 104 published repositories (84 instructed, 15 on gasp alone, 5 on a missing prep).

`check-built-2026-11-05.txt`: on the 24 fonts built for this probe, the gate agrees with the prediction 24 of 24 times (Homemade Apple passes on fontspector's gasp, Tuffy Bold on the smart_dropout prep its release lacks). verify_metadata.py `--build` passes Abril Fatface (its commit in google/fonts#11234) and fails Actor (its commit in google/fonts#11237) on hinting.
