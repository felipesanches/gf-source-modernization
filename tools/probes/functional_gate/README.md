# tools/probes/functional_gate -- evidence for tools/functional_gate.py

**Model**: Claude Opus 5.5 -- 2026-09-25

`PY=/home/fsanches/compartilhado/gftools/venv/bin/python3`, run from the workspace root.
Scratch root `$S` = `$FG_SCRATCH`, default `/home/fsanches/compartilhado/sfd-reland-scratch/functional-gate`
(builds, diffenator3 JSON, per-style verdict JSON; all regenerable, none committed).
The word lists the gate shapes live in `$S/fontheight` (`$PY tools/functional_gate.py --fetch-wordlists`
recreates them at fontheight `b23cef0f8712`; digest `c297e1013a0e5810`, printed in every verdict).

| script | question it answers | command | output |
|---|---|---|---|
| `validate.py` | What does the functional gate say about every landed style (fresh clone of `../sfd-reland-repos/<repo>`, pinned builder3, as `verify_landed.py` builds it) and about the known cases in `EXTRA.tsv`? | `$PY tools/probes/functional_gate/validate.py > tools/probes/functional_gate/RESULT.tsv` | `RESULT.tsv`: repo@HEAD, style, verdict, the seven check statuses, the first failure of each failing check |
| `mutations.py` | Does each check fail on the defect it exists for, and only that check? One release (Salsa-Regular) mutated with fontTools, one defect per copy. | `$PY tools/probes/functional_gate/mutations.py > tools/probes/functional_gate/MUTATIONS.txt` | `MUTATIONS.txt`: `OK` when the failing checks are exactly the expected ones |
| `summarize.py` | Across a `validate.py` run, how many styles fail each check, for which reasons, and which styles? | `$PY tools/probes/functional_gate/summarize.py tools/probes/functional_gate/RESULT.tsv > tools/probes/functional_gate/SUMMARY.txt` | `SUMMARY.txt`: per check, failure classes with their styles |
| `land_convert_test.py` | Does land.py's convert step, with the gate wired in, write the right commit message and verdict, without touching `../sfd-reland-repos` or `landed.tsv`? | `FAMILIES=families-next.tsv $PY tools/probes/functional_gate/land_convert_test.py rochester` (and `italiana`) | stdout: the convert commit message (Rochester: CLEAN wording, functional PASS; Italiana: "functionally different in shaping, rendering, names") |
| (verify_landed.py) | Does verify_landed.py run the gate as check 7? | `FAMILIES=families-next.tsv SCRATCH=$S/verify $PY tools/verify_landed.py rochester salsa > tools/probes/functional_gate/VERIFY_SAMPLE.txt` | `VERIFY_SAMPLE.txt`: rochester VERIFIED; salsa FAILED on shaping, names, gdef |
| `calibrate_geometry.py` | Which rendering threshold separates the outline differences the conversion makes (rounding, implied points, start point) from real ones, and does diffenator3's 32 ppem glyph test see a local deformation? | `$PY tools/probes/functional_gate/calibrate_geometry.py > tools/probes/functional_gate/CALIBRATION.txt` (pairs: validate.py's, plus the moved-point mutation; run after mutations.py) | `CALIBRATION.txt`: per pair, changed outlines bucketed by differing pixels, both measures, worst glyphs |

`EXTRA.tsv` lists pairs that are not landed repositories: Lohit-Bengali built from the
provenance-repaired source (pravins/lohit `0df83ad`), rebuilt here with
`FAMILIES=investigations/next-provenance-verify/runs/v1-lohit-repair/families.tsv OUT=$S/lohit/out SCRATCH=$S/lohit TAG=fg bash tools/baseline.sh Lohit-Bengali`
(table gate: CLEAN 0), and the verifier's own build of it.

Signals read, and what PASS means, are in the docstring of `tools/functional_gate.py`.
