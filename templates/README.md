# templates/ufr-template

The files `tools/land.py` copies into every landed repository (its `TEMPLATE_FILES`), taken from
https://github.com/googlefonts/googlefonts-project-template at 17b624b (main after #226, which hardened
`.github/workflows/build.yaml` for zizmor, the check googlefonts runs on pull requests), with one change:

- `Makefile` and `.github/workflows/build.yaml` build with gftools-builder
  (simoncozens/gftools-rust) at the revision the landing was verified with (`GFTOOLS_RUST_REV`),
  instead of the Python gftools in a venv. In `build.yaml` that is the `GFTOOLS_RUST_REV`
  variable and the "Compile gftools-builder" step; everything else equals upstream.

Check a change with zizmor (pip install zizmor; 1.32.0 reports no findings):

    zizmor --offline templates/ufr-template/.github/workflows/build.yaml
