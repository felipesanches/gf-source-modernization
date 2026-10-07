# gftools_no_production_names

**Model**: Claude Opus 5.5. **Date**: 2026-10-06.

Question: Python gftools rejected our configs' `noProductionNames: true` (gftools-rust's key;
googlefonts/fontc_crater#100, gftools-mode targets). With the change in
`noProductionNames.patch` (this directory) applied to googlefonts/gftools main at 600993df,
does the key validate, and does it keep the source's glyph names?

    git clone https://github.com/googlefonts/gftools && git -C gftools checkout 600993df
    git -C gftools apply ../noProductionNames.patch       # or: git am
    python3 -m venv venv && venv/bin/pip install -e gftools
    REPOS=<dir with the landed repositories> sh probe.sh <scratch> venv

Result on 2026-10-06 (Quantico-Regular from googlefonts/quantico; fontmake 3.12.1): both
configs validate and build; with the key, 268 glyphs and 0 names outside the source; without
it, 7 glyphs renamed to production names (mu -> uni03BC, kcommaaccent -> uni0137, dotlessj ->
uni0237, ...). gftools tests/test_builder.py: 11 passed with and without the change.

2026-10-07: the change rebased onto googlefonts/gftools main b42647c3 (the patch applies there
unchanged); tests/test_builder.py 11 passed and the probe gives the same result.
