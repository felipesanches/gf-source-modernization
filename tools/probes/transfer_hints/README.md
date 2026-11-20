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

## The rework, 2026-11-20 (rework_transfer.py, results-rework-2026-11-20.txt)

`rework_transfer.py <gftools checkout> <release.ttf> <built.ttf> <out.ttf> [<hint source>]` runs the reworked
`Lib/gftools/scripts/transfer_hints.py` (gftools-worktrees/apply-hinting, uncommitted on top of 34f59edf): font to
font, no hinting-file format. Every glyph whose built outline is the release's (the same contours up to the start
point, on-curve points halfway between two off-curves, repeated points, single-point contours and a horizontal
shift; a composite with the same components) takes the release's glyph, points, recorded box, side bearing and
program; the target is saved without recomputing boxes (a TrueType rasterizer places a glyph by its recorded box,
which a release may have stale). An instructed glyph that does not match is refused and nothing is written.

On the same 29 fonts as results-2026-11-20.txt: 29 pass the hinting check (23 with glyph programs, 6 prep only),
none refused. Each refinement was measured on the way: without the repeated-point and single-point rules 10 fonts
were refused (1 to 4 glyphs each, e.g. Share J, Tauri y: a duplicated point; Stoke's .ttfautohint: a one-point
contour); with box recomputation Stoke-Regular failed in 5 of 7225 glyph sizes (grave, acute: stale boxes).

A .ttx dump of the release as the hint source (`ttx -t GlyphOrder -t head -t maxp -t hmtx -t glyf -t fpgm -t prep
-t "cvt " -t gasp -t hdmx -t LTSH -t VDMX`, 0.6 to 1.1 MB per style) gives the same glyf, fpgm and prep and passes
too (Actor-Regular, Stoke-Regular, Volkhov-Italic).
