# templates/ufr-template

The files `tools/land.py` copies into every landed repository (its `TEMPLATE_FILES`), taken from
https://github.com/googlefonts/googlefonts-project-template at d52f47c, with these changes:

- `Makefile` and `.github/workflows/build.yaml` build with gftools-builder
  (simoncozens/gftools-rust) at the revision the landing was verified with (`GFTOOLS_RUST_REV`),
  instead of the Python gftools in a venv.
- `.github/workflows/build.yaml` is hardened for zizmor, the check googlefonts runs on pull
  requests: per-job permissions, no `${{ }}` inside `run:` scripts, actions pinned to commit
  hashes, no persisted checkout token, and no caches (the workflow also publishes releases).

Check a change with zizmor (pip install zizmor; 1.32.0 reports no findings):

    zizmor --offline templates/ufr-template/.github/workflows/build.yaml
