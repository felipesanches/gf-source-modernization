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

## What changed the picture

Converting each style's UNMODIFIED source with **fidelity flags only** -- flags that
replicate FontForge's own TTF exporter, never flags that correct the font -- left
far fewer differences than the old 19-step pipeline was compensating for
(`baseline.tsv`). Most of the rest were two converter/compiler gaps:

- **OS/2 x-height and cap height**: FontForge computes them at export
  (`SFStandardHeight`). Ported to babelfont (`--fontforge-os2-defaults`, gf-sfd-conversion
  `ca43adc`); the port agrees with an independent Python oracle on 42 of 42 sources,
  and the rule reproduces 54 of 76 released values.
- **usWeightClass**: fontc 1.0.0 ignores a single-master Glyphs source's instance
  `weightClass` (`issues/fontc-static-weight-class.md`). Carried as FEA, from the
  `.sfd`'s own `TTFWeight`, until fontc is fixed.

## Pinned toolchain

| tool | revision |
|---|---|
| babelfont | `ca43adc` on branch `gf-sfd-conversion` (upstream main `6ab2312` + PR 90 + fidelity filters + the height rule) -- **must be pushed to felipesanches/babelfont-rs before the repos are published, so the revision every convert commit cites is public** |
| gftools-builder3 | `e851b8b` (upstream tip), fontc 1.0.0 (latest release) |
| table gate | `../sfd-batch5/tools/table_gate.py` |
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
| `tools/sfd_edit.py` | Apply one documented `.sfd` edit (setfield / addfield / ensurefield / nbspwidth / renameglyph). | `$PY tools/sfd_edit.py <file.sfd> <op> <args>` |
| `tools/workarounds.py` | Which values does the toolchain lose, and carry them across from the `.sfd`. | `$PY tools/workarounds.py <file.glyphs> <file.sfd>` |
| `tools/build_babelfont.sh` | Build the pinned converter and stamp the commit it was built from. | `sh tools/build_babelfont.sh` |
| `tools/land.py` | Build one repository's history, gate it before the convert commit is written. | `$PY tools/land.py <repo> [--rebuild]` |
| `tools/verify_landed.py` | Independently re-check a landed repository from a fresh clone. | `$PY tools/verify_landed.py <repo>...` |
| `tools/push.sh` | Push what is verified; `--check` first. | `sh tools/push.sh --check` |

Probes, each with `run.sh` and `EXPECTED.txt`: `tools/probes/fontc_static_weight_class/`.

## Outputs

- `families.tsv` -- the pairing; `baseline.tsv` + `baseline/` -- the fidelity-only measurement
- `plans/<repo>.json` -- the documented `.sfd` edits for a repository, when it needs any
- `landed.tsv` -- one row per landing (last row per repository wins)
- `investigations/<unit>/FINDINGS.md`, `VERIFY.md` -- per-family root causes, each
  adversarially re-verified
- the repositories themselves: `../sfd-reland-repos/<repo>` (not in this repo)
