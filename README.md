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
| `tools/land.py` | Build one repository's history, gate it before the convert commit is written. | `$PY tools/land.py <repo> [--rebuild]` |
| `tools/verify_landed.py` | Independently re-check a landed repository from a fresh clone. | `$PY tools/verify_landed.py <repo>...` |
| `tools/push.sh` | Push what is verified; `--check` first. | `sh tools/push.sh --check` |
| `tools/metadata.py` | The google/fonts commit per family pointing at a landed repository. | `$PY tools/metadata.py <branch> <repo>...` |
| `tools/pr_body.py` | The PR body for a fork branch, derived from the branch itself. | `$PY tools/pr_body.py <repo>` |
| `tools/findings_from_results.py` | Render the investigation workflow's structured results as FINDINGS.md / VERIFY.md. | `$PY tools/findings_from_results.py investigations/workflow-journal-*.jsonl <unit>...` |

Probes: `tools/probes/fontc_static_weight_class/` (`run.sh`, `EXPECTED.txt`: fontmake 700,
fontc 400); `tools/probes/cmap_recipe/` (`run.py`; `RESULT.tsv`: per style, the codepoints
gained and lost with and without `--add-legacy-duplicate-cmap`).

## Outputs

- `families.tsv` -- the pairing; `baseline.tsv` + `baseline/` -- the fidelity-only measurement
- `plans/<repo>.json` -- the documented `.sfd` edits for a repository, when it needs any
- `landed.tsv` -- one row per landing (last row per repository wins)
- `investigations/<unit>/FINDINGS.md`, `VERIFY.md`, `results.json` -- per-family root
  causes, each adversarially re-verified; the workflow journal they came from is
  `investigations/workflow-journal-wf_67b21e98-632.jsonl`
- `issues/` -- upstream issue drafts (fontc weight class, fontc duplicate glyph name)
- the repositories themselves: `../sfd-reland-repos/<repo>` (not in this repo)
