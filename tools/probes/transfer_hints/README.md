# transfer_hints: does the minimal `gftools transfer-hints` (gftools#1248 review) keep the hinting?

Marc Foley on gftools#1248 (2026-11-16): "transfer say the gasp, fpgm and other whole tables. Then
for matching glyphs only transfer over the instruction if the direction and point counts match."

| script              | question it answers                                                                   | command                                                              |
|---------------------|---------------------------------------------------------------------------------------|----------------------------------------------------------------------|
| minimal_transfer.py | that rule on one built font, then tools/functional_gate.py's hinting check            | `python3 -I minimal_transfer.py <release.ttf> <built.ttf> <out.ttf>` |
| run.sh              | build each repository (gftools-rust 1e638bd) and run minimal_transfer.py on each font | `sh run.sh <scratch> <repo>...`                                      |

## Results, 2026-11-20 (results-2026-11-20.txt)

The 11 hinted googlefontdirectory-hg forks (sfd-reland-repos, landed 2026-11-18) and the 8 repositories
of tools/probes/hinting points-2026-11-05 (cloned from the repo archive), google/fonts c36d6f24:

| fonts                               | pass the hinting check |
|-------------------------------------|------------------------|
| 23 with glyph programs              | 1 (Stalinist One)      |
| 6 with a prep and no glyph programs | 6                      |

Of the 6450 instructed glyphs of the 23 fonts: 1184 refused (point counts differ), 0 refused on
direction, 5266 transferred, of which 1891 onto points that are not the release's (same counts,
other coordinates or order) and 3375 onto the release's points. Hinted rendering then differs in
172 (Spinnaker) to 6008 (Stoke-Regular) of the glyph sizes compared per font.

With the route #1248 implements (restoring the points the toolchain changes before attaching each
program; tools/probes/hinting land-hinting-2026-11-05.tsv), Actor, Volkhov (4 styles), Lobster Two (4)
and Share (4) passed the whole functional gate, hinting included; with the minimal rule all 13 fail.
Supermercado One was not compared (its built file name differs from the shipped one).
