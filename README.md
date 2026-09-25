# sfd-reland -- re-landing the FontForge-only families under criteria (A) and (B)

**Model**: Claude Opus 5.5 -- started 2026-09-23

Felipe's two acceptance criteria for every converted repository:

> (A) the converted sources match the available binaries;
> (B) any additional work done to the fonts is described explicitly as individual
> commits with source edits in the git history, reconstructing the font's
> development history as faithfully as we can.

The batch-6 and batch-7 landings satisfied (A) and not (B): every correction was
folded into one convert commit. This workspace rebuilds all of them from scratch
in the shape the repositories this programme already published use (verified on
100 googlefonts/* repos in the repo archive): the unmodified original, the Unified
Font Repository template, one commit per documented `.sfd` edit, and
`Convert to .glyphs with babelfont <rev>` last.

## The equivalence commit (Felipe, 2026-09-24)

Modernization adds no features. The commit METADATA.pb records is the one whose build is
FUNCTIONALLY equivalent to the binaries Google Fonts ships (same cmap, shaping, metrics,
rendering; not byte-identical). Where the release differs from the source -- a dropped
ligature, a clipped ascent, an empty GPOS -- a documented commit before the conversion
reproduces it. Any improvement is a later commit, left as future work for an onboarder's
font-update PR. `tools/metadata.py` records the conversion commit (not HEAD), states this
in `upstream_info.md`, and lists later commits plus each plan's `future_work`.

## The functional gate (2026-09-25)

The table gate reads diffenator3's `tables` section and accepts whole classes of rows
(`OS/2.fs_selection`, `head.mac_style`, a reorganised GPOS, GDEF classes, "release-stale"
hmtx bearings); names are not gated at all. The next-batch investigations showed it passing
fonts that behave differently. `tools/functional_gate.py` measures behaviour instead: cmap to
glyph name, HarfBuzz shaping compared position by position, rendering, names, per-platform
line spacing, every advance, GDEF as shaping reads it. Its docstring states each check, the
signal it reads and every threshold. `land.py` runs it after the table gate (CLEAN only if
both pass, and the convert commit says which checks failed); `verify_landed.py` runs it as
check 7. The table gate itself is unchanged.

Evidence (`tools/probes/functional_gate/`, see its README):

- **Each check catches its own defect.** 9 of 9 fontTools mutations of Salsa-Regular fail
  exactly the expected checks; the unmutated copy passes all seven (`MUTATIONS.txt`).
- **Rendering thresholds.** 4145 glyphs in 95 pairs (92 landed styles, two Lohit-Bengali
  builds, one mutation) store their outline differently. Every one the conversion rewrites
  (point structure, 1-unit rounding, start point, 1-unit stale lsb) scores 0 px on the
  geometry test; the non-zero scores are the real differences listed below and the mutation.
  One point moved 60 units scores 40 px, where diffenator3's own glyph test gives 7 of the 16
  it needs (`CALIBRATION.txt`). diffenator3's counts do not measure displacement: a 1-unit
  lsb difference on identical points scores 179 px (Kristi `a`; FreeType at the same size:
  0), a 4-unit shift 17 px (NixieOne comma). So its reports fail a font only when the
  geometry test or HarfBuzz confirms them. The rest are listed as notes.
- **Every landed style** (92 styles in 69 repositories, all CLEAN under the table gate,
  rebuilt from fresh clones): **26 PASS, 66 FAIL** (`RESULT.tsv`, `SUMMARY.txt`).

| known case | table gate | functional gate |
|---|---|---|
| Italiana-Regular (double kerning) | CLEAN | FAIL: shaping, 823 of 22201 pairs and 341742 of 515663 words; rendering, 52 words confirmed; name ID 4 |
| Salsa-Regular (no GDEF) | CLEAN | FAIL: gdef (acutecomb, gravecomb 1 -> 3); shaping, 307 of 332 base+mark, 344 of 389 kern+mark; name ID 4 |
| name ID 6 styles | CLEAN | FAIL names in 17 styles: the 16 of next-fstype-verify, plus Niconne, whose `.sfd` family name is `Nicone` |
| Lohit-Bengali at `0df83ad` (rebuilt, `EXTRA.tsv`) | CLEAN | FAIL: rendering, the 284 Bengali words, all confirmed; shaping, 13646 of 49519 words; line spacing, USE_TYPO_METRICS moves Windows and FreeType from win 760/-325/+200 to typo 750/-274/0; names |
| Rochester-Regular | CLEAN | PASS, all seven |

Failure classes the table gate hid (counts over the 92 landed styles; `SUMMARY.txt` lists them):

- name ID 4: 57 styles. The release has the `.sfd` FullName (`Italiana`); the build has `Italiana Regular`.
- name ID 2 / fsSelection / macStyle. Kristi, Miama and NovaScript are named Italic, and Kristi and NovaScript also gain the ITALIC bits. Overlock-BlackItalic loses ITALIC. Six Nova styles go from `Book` to `Regular`.
- GDEF: 15 styles. The release classes combining marks as bases; the build has no GDEF, so HarfBuzz makes them zero-width marks.
- Miama and Nosifer have no GPOS in the release, so their marks use HarfBuzz fallback positioning. The build's GPOS turns that off.
- USE_TYPO_METRICS, set by the converter for OS/2 v1-v3 releases, changes Windows line spacing in 6 styles (Kristi, Lekton x3, PatrickHand, Revalia). Where typo equals win it changes nothing and is a note.
- A stale hmtx lsb moves ink, because TrueType rasterizers place the outline at xMin - lsb. This hits NixieOne's punctuation by 4 units and Corben-Bold's AE, Lslash and lslash by 5 to 9 units. The table gate files these as RELEASE-STALE.
- Outlines differ: `.notdef` (Kristi, Nosifer, NosiferCaps, Corben-Regular, including its advance), MrBedfort `backslash` and `bracketleft`, Niconne `zero`, RougeScript's accented `I`s.
- Lekton-Bold and Lekton-Regular ligate `fi` under the release's `TUR` language system. `TUR` is not a registered tag, so only CSS `font-language-override` or similar reaches it. NovaMono loses `post.isFixedPitch`.

Hinting is reported, not gated: most releases carry an `fpgm`/`prep` or glyph programs that
the builds do not. Every `landed.tsv` row from before this date predates the gate. Re-verify
with `FAMILIES=families-next.tsv $PY tools/verify_landed.py <repo>`.

## What changed the picture

Converting each style's UNMODIFIED source with **fidelity flags only** -- flags that
replicate FontForge's own TTF exporter, never flags that correct the font -- left
far fewer differences than the old 19-step pipeline was compensating for
(`baseline.tsv`): of 42 styles, 3 were already CLEAN and 25 more differed only in the
OS/2 x-height, cap height or weight class. (The commit that recorded the baseline,
`063d57b`, says "29 more"; that count was wrong -- 25 is what `baseline.tsv` holds.)
Most of the rest were two converter/compiler gaps:

- **OS/2 x-height and cap height**: FontForge computes them at export
  (`SFStandardHeight`). Ported to babelfont (`--fontforge-os2-defaults`, gf-sfd-conversion
  `ca43adc`); the port agrees with an independent Python oracle on 42 of 42 sources,
  and the rule reproduces 54 of 76 released values.
- **The pre-2012 height rule**: FontForge builds before 4d34d21ef866 (2012-05-14) divided
  the distinct round tops by the number of glyphs. `--fontforge-height-glyph-count-mean`
  (gf-sfd-conversion `8b59bc3`), chosen by the release's FFTM stamp, closes the heights of
  HerrVonMuellerhoff, Miama, NosiferCaps and UnifrakturCook (`investigations/heights/`).
- **usWeightClass**: fontc 1.0.0 ignores a single-master Glyphs source's instance
  `weightClass` (`issues/fontc-static-weight-class.md`). Carried as FEA, from the
  `.sfd`'s own `TTFWeight`, until fontc is fixed.

The table gate accepts GAINED codepoints, which hid that `--add-legacy-duplicate-cmap`
added 1-3 codepoints to 11 landed styles (`tools/probes/cmap_recipe/RESULT.tsv`). The flag
is now never passed, and land.py and verify_landed.py require exactly the release's
codepoints.

## Pinned toolchain

| tool | revision |
|---|---|
| babelfont | `8b59bc3` on branch `gf-sfd-conversion` (upstream main `6ab2312` + PR 90 + fidelity filters + both height rules) -- **not yet upstream. A font repository may cite only a revision merged into simoncozens/babelfont-rs, never a fork: land.py refuses otherwise (`--unpublished-converter` lands for measurement only, status `*-UNPUBLISHED-CONVERTER`), and push.sh refuses a convert commit citing a revision not on upstream main. The 27 landings are blocked until these commits merge; then re-land.** |
| gftools-builder3 | `e851b8b` (upstream tip), fontc 1.0.0 (latest release) |
| table gate | `../sfd-batch5/tools/table_gate.py` at `2f43693` (contour split fixed in `cd4f827`) |
| functional gate | `tools/functional_gate.py`: HarfBuzz 12.3.2 (uharfbuzz 0.53.3), FreeType 2.13.2 (freetype-py 2.5.1), fontTools 4.61.1, diffenator3 1.1.4; word lists googlefonts/fontheight `b23cef0f8712` `static-lang-word-lists/data/diffenator` (the lists diffenator3 embeds), digest `c297e1013a0e5810` |
| releases | google/fonts `b5efa9c32e8f` |

## Tools -- what each answers, and how to run it

All Python runs with `PY=/home/fsanches/compartilhado/gftools/venv/bin/python3`.

| script | question it answers | command |
|---|---|---|
| `tools/make_families.py` | Which repository does each shipped style land in, from which unmodified base and source, against which release? Pairing decided once, explicitly. | `$PY tools/make_families.py > families.tsv` |
| `tools/baseline.sh` | Converting the unmodified source with fidelity flags only, which table rows still differ? Also the harness for trying a candidate edit (`SRC_OVERRIDE=`, `EXTRA_FLAGS=`, `DROP_FLAGS=`, `BF=`, `OUT=`, `TAG=`). | `bash tools/baseline.sh <Style>` / `--all` |
| `tools/ff_heights_oracle.py` | Are the released sxHeight/sCapHeight what FontForge's exporter computes from the source? | `$PY tools/ff_heights_oracle.py` |
| `tools/verify_heights_port.py` | Does babelfont's Rust port of that rule agree with the oracle on every real source? | `$PY tools/verify_heights_port.py <babelfont>` |
| `tools/recipe.py` | Which babelfont flags does a style get, and why? (`--check`: agrees with baseline.sh.) | `$PY tools/recipe.py <Style>` |
| `tools/sfd_edit.py` | Apply one documented `.sfd` edit (setfield / addfield / ensurefield / nbspwidth / renameglyph / renameglyphgid / scaleem / droplookup). | `$PY tools/sfd_edit.py <file.sfd> <op> <args>` |
| `tools/ff_scale_em.py` | What did FontForge 20100501's `f.em = 1024` do to each point? (Puritan; used by `scaleem`.) | imported by sfd_edit.py |
| `tools/workarounds.py` | Which values does the toolchain lose, and carry them across from the `.sfd`. | `$PY tools/workarounds.py <file.glyphs> <file.sfd>` |
| `tools/build_babelfont.sh` | Build the pinned converter and stamp the commit it was built from. | `sh tools/build_babelfont.sh` |
| `tools/land.py` | Build one repository's history, gate it before the convert commit is written (table gate, exact codepoints, functional gate: CLEAN only if all pass). | `$PY tools/land.py <repo> [--rebuild]` |
| `tools/functional_gate.py` | Does a built font BEHAVE like the shipped one? cmap to glyph name; HarfBuzz shaping (pairs, marks, rule sequences, word lists, every feature toggled, every language system); rendering (diffenator3 + FreeType outline geometry); names 1 2 4 6 16 17 21 22; per-platform line spacing; every advance; GDEF classes as shaping reads them. PASS/FAIL per check, JSON verdict. | `$PY tools/functional_gate.py <shipped.ttf> <built.ttf> [--json out.json]` (once: `--fetch-wordlists`) |
| `tools/verify_landed.py` | Independently re-check a landed repository from a fresh clone, functional gate included. | `$PY tools/verify_landed.py <repo>...` (`FAMILIES=families-next.tsv` for the next batch) |
| `tools/push.sh` | Push what is verified; `--check` first. | `sh tools/push.sh --check` |
| `tools/metadata.py` | The google/fonts commit per family pointing at a landed repository. | `$PY tools/metadata.py <branch> <repo>...` |
| `tools/pr_body.py` | The PR body for a fork branch, derived from the branch itself. | `$PY tools/pr_body.py <repo>` |
| `tools/findings_from_results.py` | Render the investigation workflow's structured results as FINDINGS.md / VERIFY.md. | `$PY tools/findings_from_results.py investigations/workflow-journal-*.jsonl <unit>...` |

Probes: `tools/probes/fontc_static_weight_class/` (`run.sh`, `EXPECTED.txt`: fontmake 700,
fontc 400); `tools/probes/cmap_recipe/` (`run.py`; `RESULT.tsv`: per style, the codepoints
gained and lost with and without `--add-legacy-duplicate-cmap`);
`tools/probes/functional_gate/` (`validate.py` -> `RESULT.tsv`: the functional gate on every
landed style and the known cases; `mutations.py` -> `MUTATIONS.txt`: each check fails on its
own defect class; `calibrate_geometry.py` -> `CALIBRATION.txt`: the rendering thresholds; its
`README.md` says how to run each).

## Outputs

- `families.tsv` -- the pairing; `baseline.tsv` + `baseline/` -- the fidelity-only measurement
- `plans/<repo>.json` -- the documented `.sfd` edits for a repository, when it needs any
- `landed.tsv` -- one row per landing (last row per repository wins). From 2026-09-25 the
  last column reads `<Style>=<table-gate rows> functional=PASS|FAIL(<checks>)` and CLEAN
  requires the functional gate; every earlier row predates it (see "The functional gate")
- `investigations/<unit>/FINDINGS.md`, `VERIFY.md`, `results.json` -- per-family root
  causes, each adversarially re-verified; the workflow journal they came from is
  `investigations/workflow-journal-wf_67b21e98-632.jsonl`
- `issues/` -- upstream issue drafts (fontc weight class, fontc duplicate glyph name)
- the repositories themselves: `../sfd-reland-repos/<repo>` (not in this repo)
