# crater-targets-2026-10-15

Inputs and crater results of the second commit of googlefonts/fontc_crater#100
(https://github.com/googlefonts/fontc_crater/pull/100), branch crater-targets-2026-10-05, which
moves the 42 families to the commits google/fonts#11121 records.

- `generated.json`: googlefonts/google-fonts-sources d7db2d8 run against google/fonts 2750b521b, the merge
  of google/fonts#11121 (`google-fonts-sources <dir> -o generated.json`, with `<dir>/google/fonts`
  a google/fonts checkout whose `origin/HEAD` points at `origin/main`).
- `merge.txt`: what `tools/crater_targets.py <the branch's targets.json before it> generated.json` reported:
  1439 -> 1440 entries; 49 revs change (the 42, TikTok Sans, and six entries google/fonts changed
  since 7085eb89a); Pushster added; googlesans and googlesans-flex kept by hand.
- `crater-compare.txt`: crater (`fontc_crater ci`) on only the 50 new or changed entries (117
  targets: 59 default mode, 58 gftools mode), googlefonts/fontc 6bbfa26d, once with gftools 0.9.93
  (fontc's current pin, A) and once with gftools 0.10.1 (the proposed pin, B); everything else identical (fontmake 3.12.1, fonttools 4.66.1). Written by
  `tools/probes/crater_gftools_pin/run_pair.sh`, which clears crater's cached results before each
  run.

| gftools | targets built | failed                                                                           |
|---------|---------------|----------------------------------------------------------------------------------|
| 0.9.93  | 61 of 117     | 54 gftools-mode targets of the 42 ("Invalid configuration file"); TikTok Sans x2 |
| 0.10.1  | 115 of 117    | TikTok Sans x2                                                                   |

0.9.93's config schema does not know `productionNames`, so the 42 need the pin bump. TikTok Sans
failed in both modes at its previous rev (TikTok/TikTokSans baa2f38, crater run of 2026-10-05) too: its designspace
names UFOs that its Makefile generates (scripts/build/glyphsToUFO.py).

To re-run (about 30 minutes, after `cargo build --release -p fontc_crater -p fontc -p
otl-normalizer` with RUSTUP_TOOLCHAIN=1.97.1 in the fontc checkout):

    python3 - old.json new.json subset.json   # the subset step of tools/crater_local.sh
    RUSTUP_TOOLCHAIN=1.97.1 sh tools/probes/crater_gftools_pin/run_pair.sh <fontc 6bbfa26d> \
        <venv with fontc's requirements.txt> <same venv with gftools 0.10.1> subset.json <scratch>

`<scratch>/cache/google/fonts` should be a google/fonts checkout at 2750b521b, or crater clones
all of google/fonts.
