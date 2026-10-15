# crater-targets-2026-10-15

Inputs and crater results of the second and third commits of googlefonts/fontc_crater#100
(https://github.com/googlefonts/fontc_crater/pull/100), branch crater-targets-2026-10-05.

**Model**: Claude Opus 5.5. **Date**: 2026-10-15.

## The targets

- `generated.json`: googlefonts/google-fonts-sources d7db2d8 run against google/fonts 2750b521b,
  the merge of google/fonts#11121 (`google-fonts-sources <dir> -o generated.json`, with
  `<dir>/google/fonts` a google/fonts checkout whose `origin/HEAD` points at `origin/main`).
  `merge.txt`: what `tools/crater_targets.py <the branch's targets.json before it> generated.json`
  reported: 1439 -> 1440 entries; 49 revs change (the 42, TikTok Sans, and six entries google/fonts
  changed since 7085eb89a); Pushster added; googlesans and googlesans-flex kept by hand.
- `generated-2.json`, `merge-2.txt`: the same against google/fonts b7c8331cf, the merge of
  google/fonts#11122 (Google Sans' source block): googlesans is now generated, at v14.000
  (5c8f512c); only its rev changes; googlesans-flex stays hand-kept.

Every generated change is kept, not only ours: targets.json is a snapshot of google/fonts at its
`fonts_repo_sha`, and crater reads override configs (google/fonts/ofl/...) at that commit.

## crater on the changed entries

`crater-fontc-main.txt`: crater as it runs today -- googlefonts/fontc main da343d39 with its own
`resources/scripts/requirements.txt` (gftools 0.10.3, fontmake 3.12.2, fonttools 4.67.0) -- on the
51 entries the two commits add or change (119 targets):

| result                         | targets                                                                 |
|--------------------------------|-------------------------------------------------------------------------|
| build                          | 116, including all 108 of the 42 families (54 default, 54 gftools mode) |
| fail in fontc only             | GoogleSans-Italic.designspace (default)                                 |
| fail in both compilers         | TikTok Sans x2 (default, gftools)                                       |
| repository reported, not built | font_tiny5, font-namdhinggo, pushster ("missing source")                |

- Google Sans Italic: GoogleSansItalic-opsz18-wght380-GRAD0.ufo/fontinfo.plist at v14.000 has
  `<integer>1509       </integer>` (openTypeOS2WinAscent, trailing spaces); fontc rejects it
  (InvalidIntegerString), fontmake (plistlib) accepts it. It built at the previous rev, fce0e066.
- TikTok Sans failed the same way at its previous rev (crater run of 2026-10-05): its designspace
  names UFOs that its Makefile generates (scripts/build/glyphsToUFO.py).
- font_tiny5 and font-namdhinggo failed in crater's 2026-10-05 run too. Pushster is new: its
  METADATA.pb copies the upstream `sources/config.yaml` into google/fonts, where
  google-fonts-sources reads it as an override, so `Lobster.glyphs` is looked for at the
  repository root instead of in `sources/`.

Run: build `fontc_crater`, `fontc` and `otl-normalizer` (`cargo build --release -p ...`) in the
fontc checkout, make a venv with `pip install -r resources/scripts/requirements.txt` run from the
fontc root (the file names `-e file:./ttx_diff`), write the subset (the step of
`tools/crater_local.sh`), clear `<cache>/crater_cached_results`, then from the fontc root:

    RUSTUP_TOOLCHAIN=1.97.1 PATH=<venv>/bin:$PATH ./target/release/fontc_crater ci subset.json --cache <cache> --out <out>

crater runs `cargo build` itself, so the active toolchain must be one fontc main accepts (>= 1.96).
`<cache>/google/fonts` should be a google/fonts checkout at the targets' `fonts_repo_sha`, or crater
clones all of google/fonts.

## Earlier: gftools 0.9.93 vs 0.10.1 (before fontc main moved its pin)

`crater-compare.txt`: the first 50 entries on fontc 6bbfa26d, once with gftools 0.9.93 and once
with 0.10.1 (`tools/probes/crater_gftools_pin/run_pair.sh`). 0.9.93 fails the 54 gftools-mode
targets of the 42 ("Invalid configuration file": it does not know `productionNames`); 0.10.1
builds 115 of 117 (TikTok Sans x2 fail). fontc main has pinned gftools 0.10.3 since 2026-10-12
(googlefonts/fontc 8a269904, 90d3579a), so the table above is what crater does today.
