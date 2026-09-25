# exclude_dflt vs feaLib: probe harness

Review of babelfont-rs branch `fix-fontforge-exclude-dflt` (2026-09-25).

Question: does every language system of a font converted from SFD get exactly
the lookups the SFD registers for it (FontForge lookups.c
SFLookupsInScriptLangFeature, exact language match) when the emitted FEA is
compiled by fontTools feaLib (fontmake) and by fea-rs (fontc)?

## Files

| file | question it answers | command |
|---|---|---|
| `fealib_langsys.py` | which lookups does feaLib put under each langsys for a hand-written FEA? | `python fealib_langsys.py head-shape.fea` |
| `base-shape.fea` | the shape upstream main 91bf8bb emits for the branch's unit-test SFD (`language XXX;` repeated per lookup) | as above |
| `head-shape.fea` | the shape 201619f emits (same, with `exclude_dflt`) | as above |
| `grouped-shape.fea` | the shape d992e2b emits (each langsys once per feature) | as above |
| `check_sfd_vs_fealib.py` | real converter output, compiled by feaLib: per (table, script, lang, feature), missing/extra lookup names vs the SFD `Lookup:` lines | `python check_sfd_vs_fealib.py FONT.sfd features.fea glyphorder.txt` |
| `check_sfd_vs_binary_counts.py` | same check for a binary where names are gone (fea-rs output): lookup counts per langsys/feature | `python check_sfd_vs_binary_counts.py FONT.sfd features.fea FONT.ttf` |
| `run.sh` | runs both checks on Varela-Regular and Poly-Italic | `PY=<python with fontTools> ./run.sh <babelfont bin> <outdir>` |
| `201619f-exclude-dflt-only.patch` | the branch commit before the review (exclude_dflt only), to rebuild that state on 91bf8bb | `git am` onto 91bf8bb |

Signal: the last line, `MISMATCHES n of m`. Pass is `n = 0`. aalt is skipped
(no script/language statements allowed in it; separate issue).

Inputs: `ofl/varela/src/Varela-Regular-TTF.sfd` and
`ofl/poly/src/Poly-Italic-TTF.sfd` from the repo archive
`googlefonts/googlefontdirectory-hg.git` at 52f780bc9d197280a9f430574e179a5f233c56b6.
Build the CLI with `cargo build -p babelfont --features cli --bin babelfont`.
The generated SFD/UFO/TTF files are regenerable and not committed.

## Results (fontTools 4.62.1 and 4.61.1 agree; fea-rs 1.0.0 as locked by babelfont)

| babelfont | Varela, feaLib | Varela, fea-rs | Poly-Italic, feaLib |
|---|---|---|---|
| 91bf8bb upstream main (\*) | 6 of 161 (extra: inherited dflt lookups) | not run here | 0 of 18 |
| 201619f exclude_dflt only | 16 of 161 (missing: lookups shared with dflt, e.g. frac 7/8 in AZE CRT DEU MOL ROM TRK) | 0 of 161 | 0 of 18 |
| d992e2b exclude_dflt + one langsys per feature | 0 of 161 | 0 of 161 | 0 of 18 (fea-rs 0 of 18) |

(\*) 91bf8bb's FEA is 201619f's with ` exclude_dflt` removed, since that flag
was 201619f's only code change (`sed 's/ exclude_dflt;/;/'`).

Varela's fea-rs GSUB and GDEF are byte-identical between 201619f and d992e2b
(GSUB sha256 7bedef29c35f19e3..., GDEF 31ea19b02c99984d...): grouping changes
only the FEA text for fontc.

Why: feaLib `Builder.set_language` (4.61/4.62 and main) removes the script's
dflt lookups from a language each time `language XXX exclude_dflt;` is seen,
so a language repeated per lookup loses what it shares with dflt. fea-rs
`ActiveFeature::set_system` fills a language only on its first statement.
FontForge's own export (featurefile.c at 20230101) names each language once
per feature.
