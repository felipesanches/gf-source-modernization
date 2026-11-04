# Re-land with the hardened template (2026-11-04)

Question: do the 81 landed-but-unpushed repos still land CLEAN, with the same per-style figures, once `templates/ufr-template/.github/workflows/build.yaml` is hardened for zizmor (templates/README.md says how)?

Answer: yes. All 81 are CLEAN, with the same commit count, verdict and figures as their previous landed.tsv rows. Every repo's `build.yaml` is byte-identical to the vendored template, and zizmor 1.32.0 reports no findings on it.

Run (italiana first, then the other 80):

    sh tools/reland/reland_same_converter.sh logs/reland-template-2026-11-04 <repo>...

The script picks the babelfont tree from the babelfont revision named in each repo's convert commit, and runs `land.py --rebuild` with `FAMILIES=families-binary.tsv`.

- `summary.txt`: one line per repo (verdict, commit count, per-style figures)
- `<repo>.log`: the land.py output

The landed commit ids (`CLEAN @ <id>` in the raw output) are removed from these copies: they are commits of font repositories not yet pushed. landed.tsv keeps them locally.
