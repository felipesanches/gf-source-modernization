# crater_builds -- will fontc_crater build the landed repositories?

**Model**: Claude Opus 5.5. **Date**: 2026-10-05.

Question: before adding the 42 repositories of google/fonts#11077 to fontc_crater's
targets.json, will crater's targets build? Crater makes two targets per source
(fontc/fontc_crater/src/ci.rs): a default one (fontc vs fontmake on the source) and a
gftools-mode one (ttx_diff runs Python gftools builder on the repository's config.yaml).

    sh crater_builds.sh ~/compartilhado/tmp/crater-builds $(cat ../../../push-2026-10-03.txt)

Result on 2026-10-05 (repos at the pushed HEADs, gftools venv: fontmake 3.11.1,
glyphsLib 6.12.7, gftools at 9bb882a4):

- default mode, fontmake: 54 of 54 sources build. (fontc compiled the same sources in the
  landing gate, logs/reland-2026-10-05-push42b.)
- gftools mode: FAILS -- "unexpected key not in schema 'noProductionNames'", then
  "ValueError: Invalid configuration file". The configs set `noProductionNames: true`
  (gftools-rust's key, tools/recipe.py builder_keys); Python gftools' GOOGLEFONTS_SCHEMA
  has no such key (absent at gftools origin/main 600993df too). Python gftools spells it
  `extraFontmakeArgs: --no-production-names`, which gftools-rust does not read.

## 2026-10-22: the binary-only families (babelfont branch 2026-10-22 at 943b9aa)

Crater's own Python pins this time: a venv from googlefonts/fontc main's
resources/scripts/requirements.txt (gftools 0.10.4, fontmake 3.12.2, glyphsLib 6.16.2),
without its local ttx_diff project:

    PYBIN=<that venv>/bin GFTOOLS_ALL=1 sh crater_builds.sh <scratch> <the 28 repos>

Result (results-2026-10-22-babelfont-943b9aa.txt): default mode 4 of 41 sources build;
gftools mode fails for all 28 with "ValueError: Unknown name language: en". The TTF reader
stored each Macintosh English name record under its BCP-47 tag `en`, which the .glyphs
then names as a language; glyphsLib knows only Glyphs' tags (dflt, ENG, ...). fontc built
them (the landing gate), so only crater's fontmake side would fail. Fixed in
ttf-static-font-fidelity by a reader commit keying name records as the SFD reader does;
after it, fontmake builds Akronim, PT Sans and Do Hyeon (each language = dflt only).
