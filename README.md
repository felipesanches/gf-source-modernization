# gf-source-modernization

Evidence for the Google Fonts source-modernization work: converting families whose only
sources are in a legacy format (FontForge `.sfd` so far; FontLab `.vfb` next) into
repositories that build with today's toolchain (babelfont-rs, gftools-builder, fontc), and
showing that each rebuild is functionally equivalent to the binaries Google Fonts ships.

Every converted font repository (`github.com/googlefonts/<family>`) cites this repository at a
fixed revision. What it cites is here:

| path                                              | what it holds                                                                                                                                                                                                                                                       |
|---------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `tools/land.py`                                   | builds a font repository's layered history: the original sources, the Unified Font Repository template, one commit per documented source edit, the conversion last                                                                                                  |
| `tools/table_gate.py`, `tools/functional_gate.py` | the two gates every rebuild must pass against the released binaries (tables; then cmap, shaping, rendering, names, line spacing, advances, GDEF, hinting)                                                                                                                    |
| `tools/verify_landed.py`, `tools/push.sh`         | re-check a landed repository; push only what is CLEAN (or CLEAN-DISCLOSED with `ALLOW_DISCLOSED=1`: every remaining gate difference is in the plan's `accepted` list, word for word), built with published tools, and cites a published revision of this repository |
| `tools/recipe.py`, `tools/sfd_edit.py`            | the converter options per style; the source-edit operations the plans use                                                                                                                                                                                           |
| `families.tsv`, `families-next.tsv`               | which source revision each released style is paired with                                                                                                                                                                                                            |
| `plans/<family>.json`                             | the documented source edits of a family (one commit each) and its disclosed known differences                                                                                                                                                                       |
| `logs/`                                           | every measurement run, per family                                                                                                                                                                                                                                   |
| `investigations/`                                 | the research behind each edit, rule and disclosure                                                                                                                                                                                                                  |
| `templates/ufr-template/`                         | the repository template the font repositories adopt                                                                                                                                                                                                                 |

**Rule: everything a converted font repository refers to is public.** Every commit id,
evidence file and URL its commit messages and README cite must resolve publicly before it
is pushed; `tools/public_refs.py` checks this and `tools/push.sh` refuses otherwise.

Rerun a family: `python3 tools/land.py <family> --rebuild` (see `tools/land.py` for the
environment it expects). Many notes and scripts name absolute paths on the author's
workstation (`/home/fsanches/compartilhado/...`); they are kept as written, since they are
part of the record. Work done with an AI agent (Claude) under the guidance of
@felipesanches.

---

# gf-source-modernization -- re-landing the FontForge-only families under criteria (A) and (B)

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

- **Each check catches its own defect.** 18 of 18 fontTools mutations fail exactly the
  expected checks: 11 of Salsa-Regular (gasp and prep among them) and 7 of the instructed
  Actor-Regular (a glyph program removed, a cvt value, a contour start rotated, the
  smart_dropout setup appended to its prep, head flag 3 cleared; fontspector's gasp in place of its own passes); both
  unmutated copies pass all eight (`MUTATIONS.txt`, 2026-11-05).
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

| known case                                        | table gate | functional gate                                                                                                                                                                                  |
|---------------------------------------------------|------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Italiana-Regular (double kerning)                 | CLEAN      | FAIL: shaping, 823 of 22201 pairs and 341742 of 515663 words; rendering, 52 words confirmed; name ID 4                                                                                           |
| Salsa-Regular (no GDEF)                           | CLEAN      | FAIL: gdef (acutecomb, gravecomb 1 -> 3); shaping, 307 of 332 base+mark, 344 of 389 kern+mark; name ID 4                                                                                         |
| name ID 6 styles                                  | CLEAN      | FAIL names in 17 styles: the 16 of next-fstype-verify, plus Niconne, whose `.sfd` family name is `Nicone`                                                                                        |
| Lohit-Bengali at `0df83ad` (rebuilt, `EXTRA.tsv`) | CLEAN      | FAIL: rendering, the 284 Bengali words, all confirmed; shaping, 13646 of 49519 words; line spacing, USE_TYPO_METRICS moves Windows and FreeType from win 760/-325/+200 to typo 750/-274/0; names |
| Rochester-Regular                                 | CLEAN      | PASS, all seven                                                                                                                                                                                  |

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

| tool             | revision                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
|------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| babelfont        | upstream main (`d7f67ca9`, #131 merged 2026-10-29; `a93e1325` today) for every landing that cites it. A font repository may cite only a revision merged into simoncozens/babelfont-rs, never a fork: land.py refuses otherwise (`--unpublished-converter` lands for measurement only, status `*-UNPUBLISHED-CONVERTER`), and push.sh refuses a convert commit citing a revision not on upstream main. Two sanctioned exceptions (land.py `BF_FORK_BRANCHES`, accepted only as GitHub serves them): branch `2026-10-22` of felipesanches/babelfont-rs (`58eedc82`, cited by the 27 published binary-only repositories; its content is #131) and branch `2026-11-02` (`26fdcfa9` = upstream main `a93e1325` + the eight commits of #117, typographic-family-names and the IDs 1/16 fix, cherry-picked, linear; verified `logs/babelfont-verify-2026-11-02`: fmt, clippy, 384 passed, the same 11 external-data failures as main; its tree equals the retired merge branch `2026-10-23` at `50ea5d2d` merged with main, `git merge-tree`, apart from Cargo.toml's version lines). |
| gftools-builder3 | `e851b8b` (upstream tip), fontc 1.0.0 (latest release)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| table gate       | `../sfd-batch5/tools/table_gate.py` at `2f43693` (contour split fixed in `cd4f827`)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| functional gate  | `tools/functional_gate.py`: HarfBuzz 12.3.2 (uharfbuzz 0.53.3), FreeType 2.13.2 (freetype-py 2.5.1), fontTools 4.61.1, diffenator3 1.1.4; word lists googlefonts/fontheight `b23cef0f8712` `static-lang-word-lists/data/diffenator` (the lists diffenator3 embeds), digest `c297e1013a0e5810`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| releases         | google/fonts `b5efa9c32e8f`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |

## Tools -- what each answers, and how to run it

All Python runs with `PY=/home/fsanches/compartilhado/gftools/venv/bin/python3`.

| script                               | question it answers                                                                                                                                                                                                                                                                                                                                                                      | command                                                                                                    |
|--------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------|
| `tools/make_families.py`             | Which repository does each shipped style land in, from which unmodified base and source, against which release? Pairing decided once, explicitly.                                                                                                                                                                                                                                        | `$PY tools/make_families.py > families.tsv`                                                                |
| `tools/baseline.sh`                  | Converting the unmodified source with fidelity flags only, which table rows still differ? Also the harness for trying a candidate edit (`SRC_OVERRIDE=`, `EXTRA_FLAGS=`, `DROP_FLAGS=`, `BF=`, `OUT=`, `TAG=`).                                                                                                                                                                          | `bash tools/baseline.sh <Style>` / `--all`                                                                 |
| `tools/ff_heights_oracle.py`         | Are the released sxHeight/sCapHeight what FontForge's exporter computes from the source?                                                                                                                                                                                                                                                                                                 | `$PY tools/ff_heights_oracle.py`                                                                           |
| `tools/verify_heights_port.py`       | Does babelfont's Rust port of that rule agree with the oracle on every real source?                                                                                                                                                                                                                                                                                                      | `$PY tools/verify_heights_port.py <babelfont>`                                                             |
| `tools/recipe.py`                    | Which babelfont flags does a style get, and why? (`--check`: agrees with baseline.sh.)                                                                                                                                                                                                                                                                                                   | `$PY tools/recipe.py <Style>`                                                                              |
| `tools/sfd_edit.py`                  | Apply one documented `.sfd` edit (setfield / addfield / ensurefield / nbspwidth / renameglyph / renameglyphgid / scaleem / droplookup).                                                                                                                                                                                                                                                  | `$PY tools/sfd_edit.py <file.sfd> <op> <args>`                                                             |
| `tools/ff_scale_em.py`               | What did FontForge 20100501's `f.em = 1024` do to each point? (Puritan; used by `scaleem`.)                                                                                                                                                                                                                                                                                              | imported by sfd_edit.py                                                                                    |
| `tools/workarounds.py`               | Which values does the toolchain lose, and carry them across from the `.sfd`.                                                                                                                                                                                                                                                                                                             | `$PY tools/workarounds.py <file.glyphs> <file.sfd>`                                                        |
| `tools/build_babelfont.sh`           | Build the pinned converter and stamp the commit it was built from.                                                                                                                                                                                                                                                                                                                       | `sh tools/build_babelfont.sh`                                                                              |
| `tools/verify_babelfont_branches.sh` | Does each babelfont-rs branch pass CI's gates (fmt, clippy, tests) on its own? One worktree at a time in one clean target (`cargo clean -p babelfont -p sr-aef` first; a shared target replays another worktree's build): `sh tools/verify_babelfont_branches.sh <tag> <worktree>...` -> `logs/babelfont-verify-<tag>/summary.tsv`.                                                      |                                                                                                            |
| `tools/land.py`                      | Build one repository's history, gate it before the convert commit is written (table gate, exact codepoints, functional gate: CLEAN only if all pass).                                                                                                                                                                                                                                    | `$PY tools/land.py <repo> [--rebuild]`                                                                     |
| `tools/functional_gate.py`           | Does a built font BEHAVE like the shipped one? cmap to glyph name; HarfBuzz shaping (pairs, marks, rule sequences, word lists, every feature toggled, every language system); rendering (diffenator3 + FreeType outline geometry); names 1 2 4 6 16 17 21 22; per-platform line spacing; every advance; GDEF classes as shaping reads them. PASS/FAIL per check, JSON verdict.           | `$PY tools/functional_gate.py <shipped.ttf> <built.ttf> [--json out.json]` (once: `--fetch-wordlists`)     |
| `tools/verify_landed.py`             | Independently re-check a landed repository from a fresh clone, functional gate included.                                                                                                                                                                                                                                                                                                 | `$PY tools/verify_landed.py <repo>...` (`FAMILIES=families-next.tsv` for the next batch)                   |
| `tools/push.sh`                      | Push what is verified; `--check` first.                                                                                                                                                                                                                                                                                                                                                  | `sh tools/push.sh --check`                                                                                 |
| `tools/metadata.py`                  | The google/fonts commit per family pointing at a landed repository.                                                                                                                                                                                                                                                                                                                      | `$PY tools/metadata.py <branch> <repo>...`                                                                 |
| `tools/rekey.py`                     | Does a landed repository still build the shipped fonts with `productionNames: false` (the renamed key) and the gftools-rust that reads it? Commits "Builder config: ..." after rebuilding and gating, appends to landed.tsv.                                                                                                                                                             | `[B3=... B3_NOTE=... NEW_PIN=...] $PY tools/rekey.py [--redo] <repo>...`                                   |
| `tools/production_names_finalize.sh` | Once the gftools-rust productionNames change is merged: pin it (land.py, template CI; fontc from its Cargo.lock), build it, redo the 42 provisional rekey commits with it, and run push.sh --check and check_publishable.py.                                                                                                                                                             | `sh tools/production_names_finalize.sh <merged gftools-rust rev>`                                          |
| `tools/verify_metadata.py`           | Is a google/fonts branch from metadata.py right to submit? One family per commit; METADATA.pb parses; the recorded commit is on the repository's branch on GitHub; every mapped file exists on both sides; `--build` rebuilds each repository at that commit and compares its outputs with the mapping; the added upstream_info.md text is ASCII and cites only public commits and URLs. | `$PY tools/verify_metadata.py --fetch --build <google/fonts worktree>`                                     |
| `tools/crater_targets.py`            | What should fontc_crater's targets.json say for the current google/fonts, with the smallest diff? Merges google-fonts-sources output into the current file: generated entries are the truth, the hand-kept private entries (googlesans, googlesans-flex) stay verbatim, nothing unchanged moves.                                                                                         | `google-fonts-sources <dir> -o gen.json; python3 tools/crater_targets.py targets.json gen.json > new.json` |
| `tools/check_publishable.py`         | Does any text we are about to publish refer to something that is not public? Every unpublished commit (message and added lines) and every PR text: no workstation path, every commit id on a published branch (or served by GitHub, flagged off-branch), every github.com URL answering 200. Run it before handing anything over for a push.                                             | `python3 tools/check_publishable.py --fetch <repo>:<unpushed range>... <pr-body.md>...`                    |
| `tools/crater_local.sh`              | Do the targets a fontc_crater PR adds build in crater itself, in both modes, before the PR is sent? Runs `fontc_crater ci` on only the new entries.                                                                                                                                                                                                                                      | `sh tools/crater_local.sh <old targets.json> <new targets.json> <scratch>`                                 |
| `tools/pr_body.py`                   | The PR body for a fork branch, derived from the branch itself.                                                                                                                                                                                                                                                                                                                           | `$PY tools/pr_body.py <repo>`                                                                              |
| `tools/findings_from_results.py`     | Render the investigation workflow's structured results as FINDINGS.md / VERIFY.md.                                                                                                                                                                                                                                                                                                       | `$PY tools/findings_from_results.py investigations/workflow-journal-*.jsonl <unit>...`                     |

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

## The VFB batch (2026-10-29)

The families whose source of record is a FontLab Studio 5 `.vfb`: `scope/census.tsv`'s
class `vfb` (130) plus the `sfd+vfb` families whose releases carry no FFTM table (13; not
exported by FontForge, so the `.vfb` is the likelier master), static only, none handled
by an earlier list. 143 families; 135 pair (194 styles), 16 styles do not: the
multiple-master sources of Arvo, Karla Tamil Inclined/Upright, Proza Libre and Ubuntu
Mono (the VFB plan's decision D3). The reader is upstream babelfont's (vfbreader 0.1.5);
what it does not read yet -- the TrueType/OS/2 block, family and style names, native
kerning and kerning classes, anchors -- is the 2026-07 fix series, re-ported onto
upstream main `b24ffd03` as branches `vfb-names`, `vfb-truetype-info-2026-10-29`,
`vfb-kerning-2026-10-29`, `vfb-filters-2026-10-29` (integration branch
`vfb-integration-2026-10-29`).

| what                                                                                                                      | where / command                                                                                                                                                                                                                          |
|---------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| pairing (rules in the docstring; the log says which fired)                                                                | `/home/fsanches/compartilhado/vfblib-py-venv/bin/python3 tools/pair_vfb.py > families-vfb.tsv 2> logs/pair_vfb.log`                                                                                                                      |
| the flags a `.vfb` style gets                                                                                             | `tools/recipe.py` `flags_for_vfb`: `VFB_BASE` plus `--correct-path-direction` unless the release mixes directions; no FontForge filter                                                                                                   |
| fidelity-only baseline on upstream babelfont (`b24ffd03`)                                                                 | `TABLES=families-vfb.tsv OUT=../vfb-reland-repos LANDED=landed-vfb.tsv BF_TREE=../babelfont-rs-worktrees/vfb-baseline sh tools/reland_all.sh <tag>`; run: `logs/reland-vfb-baseline-2026-10-29/`                                         |
| the same with the ported fixes (measurement only)                                                                         | `BF_TREE=../babelfont-rs-worktrees/vfb-integration LAND_ARGS=--unpublished-converter ...` with its own `OUT=` and `LANDED=`; run: `logs/reland-vfb-fixes-2026-10-29/` (integration `40e07b57`)                                           |
| what fails, per check and cause; what a converter change fixed or broke                                                   | `python3 -I tools/reland_triage.py <tag>` -> `logs/reland-<tag>/triage.tsv`; `python3 -I tools/compare_runs.py <old tag> <new tag>`                                                                                                      |
| which rule FontLab's export used for each table value (194 styles)                                                        | `tools/probes/vfb_rules/vfb_vs_release.py` -> `rules-2026-10-29.txt` (tallies), `vfb-vs-release-2026-10-29.tsv` (raw values); the five rules are branch `vfb-export-rules-2026-10-29`, PR body `pr-bodies/babelfont-vfb-export-rules.md` |
| the weight and width classes a `.vfb` states                                                                              | on the converted instance; `workarounds.instance_classes_fea` restates them as FEA (fontc 1.0.0 drops a single master's instance classes, `issues/fontc-static-weight-class.md`)                                                         |
| `--infer-mark-category` on a spacing accent with `_top`                                                                   | branch `infer-mark-category-encoded-2026-10-29` (encoded non-mark glyphs keep their category), PR body `pr-bodies/babelfont-infer-mark-category-encoded.md`; Atomic Age's 15 zeroed advances                                             |
| the full re-land on the final recipe (five rules, no mark inference, GOADB where present)                                 | run: `logs/reland-vfb-fixes4-2026-10-29/` (integration `dfdc141f`): blocking rows 1056 (baseline) -> 609; `compare-vfb-baseline-2026-10-29.tsv`, `compare-vfb-fixes-2026-10-29.tsv`, `triage.tsv` beside it                              |
| a `.vfb` beside a makeotf `GlyphOrderAndAliasDB` (the Mukta families)                                                     | `recipe.flags_for_vfb` adds `--glyph-order-and-alias-db=<the .vfb's path>` (the filter searches upwards); Mukta Mahee regains U+0964/U+0965, Mukta Vaani U+0ABF                                                                          |
| where every repository stands at GitHub: EMPTY (created for us, waiting), MISSING (to create), PUBLISHED, or content (PR) | `python3 -I tools/repo_status.py` -> `repos-status.tsv` + the groups PR-QUEUE section 4 lists (rerun before each batch)                                                                                                                  |
| verdicts                                                                                                                  | `landed-vfb.tsv` / `landed-vfb-fixes.tsv` (last row per repository wins), logs under `logs/reland-<tag>/`                                                                                                                                |

A landing on a librefonts mirror (kind `fork`) is branch `modernize-vfb-to-glyphs` on
the googlefonts fork that does not exist yet; a monorepo family (kind `hg`) is a fresh
repository; an upstream repository (kind `upstream`) a branch for a pull request.
