crater-local-2026-11-08: does the one entry of the 2026-11-08 targets update (googlefonts/intel-one-mono 06572f3e, sources/config.yaml; google/fonts#11258) build in fontc_crater, in both modes, before its targets PR? (tools/crater_local.sh; cmyr asked for this on #100.)

Targets: fontc_crater main's targets.json (a2e66c9) and the branch crater-targets-2026-11-08 (logs/crater-targets-2026-11-08). fontc: googlefonts/fontc main d73bdfae (the revision of fontc_crater's last CI run, 8ccbcff), RUSTUP_TOOLCHAIN=1.97.1; venv from its resources/scripts/requirements.txt (`pip-freeze.txt`: gftools 0.10.8, fontmake 3.12.2, glyphsLib 6.17.1). `subset.json` is the entry run, `summary.txt` the result (tools/crater_summary.py; the scratch directory written as `<scratch>`, TMPDIR as `<tmp>`).

  RUSTUP_TOOLCHAIN=1.97.1 sh tools/crater_local.sh <a2e66c9 targets.json> <crater-targets-2026-11-08 targets.json> <scratch>

| target (06572f3e)                       | default   | gftools                  |
|-----------------------------------------|-----------|--------------------------|
| masters/IntelOneMono.designspace        | identical | fontc failed (see below) |
| masters/IntelOneMono-Italic.designspace | identical | fontc failed (see below) |

gftools mode: the repository's config.yaml sets `extraFontmakeArgs: "--fea-include-dir=features"`; gftools passes it to fontc as well, and fontc rejects it ("error: unexpected argument '--fea-include-dir' found"). fontmake builds both.

The entry it replaces, intel/intel-one-mono 99e2d6c with the google/fonts override config, in fontc_crater's CI run 8ccbcff (results/2026-11-06-154211.json): Roman built in both modes with differences (fvar, name), Italic failed in both modes (fontc).
