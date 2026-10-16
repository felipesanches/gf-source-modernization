# converter-ab-2026-10-16

`converter_ab.py` runs of 2026-10-16 over the 109 shipped fonts of families-binary.tsv (50
repositories: the 48 landed, and Almarai and Dongle, withdrawn from this track). Each font is
converted by both babelfonts as land.py converts it; the `.glyphs` files are compared with each
`date` dropped and the master UUIDs numbered.

| file              | A                                               | B                                                                                                       | result                |
|-------------------|-------------------------------------------------|---------------------------------------------------------------------------------------------------------|-----------------------|
| `reader-only.txt` | the measured babelfont (`babelfont/rebuild.sh`) | upstream d44f2bdc + `babelfont/sr-aef-uncompile-fixes/` + `babelfont/ttf-static-font-fidelity/`         | 29 SAME, 21 DIFFERENT |
| `refactor.txt`    | B of `reader-only.txt`                          | upstream 3e3b6dcf + `babelfont/pr-2026-10-16/sr-aef-uncompile-fixes/` + `.../ttf-static-font-fidelity/` | 50 SAME               |

`reader-only.txt` answers which babelfont PRs each family needs. `causes.txt` (`sh
ab_causes.sh reader-only.txt <scratch>`) counts each DIFFERENT family's changed lines with a
Windows language id (the localized Name Table Entry records of simoncozens/babelfont-rs#117)
and the others (name IDs 16/17 and the typographic familyName of typographic-family-names):

| needs                    | families                                                                                                                                                        |
|--------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------|
| only the two reader PRs  | the other 29 of the 48                                                                                                                                          |
| #117                     | blackandwhitepicture, blackhansans, cutefont, dokdo, eastseadokdo, gamjaflower, gugi, himelody, nanumbrushscript, nanumpenscript, poorstory, songmyung, stylish |
| typographic-family-names | averialibre, averiasanslibre, averiaseriflibre, lato, sunflower (and almarai, dongle)                                                                           |
| both                     | nanumgothic                                                                                                                                                     |

`refactor.txt` answers whether reorganizing the two reader PR branches (2026-10-16: rebased on
upstream 3e3b6dcf, follow-up fixes folded into the commits they complete, comments and
messages shortened, one mark rule shared by categories and kerning) changed any conversion:
none did. `babelfont/pr-2026-10-16/` applied to upstream 3e3b6dcf gives the branches' tree
exactly.

Rerun: build each babelfont with `cargo build --release -p babelfont --features cli`, then
`GF=<google/fonts clone> ARCHIVE=<repo archive> python3 converter_ab.py <A> <B> <scratch>`;
`fixed-pitch.txt` is `fixed_pitch.py`'s output with the same GF and ARCHIVE.
