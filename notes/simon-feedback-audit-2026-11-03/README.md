# Audit 2026-11-03: everything we propose or plan, against Simon's feedback

Question answered: which of our tool branches, PR texts, pipeline steps and landed font repositories go
against review feedback Simon Cozens has already given, and what is the right shape for each?

Sources of the feedback: every comment by others on simoncozens/babelfont-rs since 2026-09-01
(tools/probes/open_prs/comments.sh; 25 by Simon), the GitHub search `involves:felipesanches
commenter:simoncozens` (38 items since 2026-05-01), google/fonts#10490, and the earlier rules kept in
memory (anonymous tuples, comment style). Reviews: a-open-pr-branches.md (the 14 open PR branches +
2 new), b-vfb-branches.md (the unproposed VFB series), c-pipeline-and-repos.md (recipe, plans, landed
repos, gftools-rust/glyphslib-rs branches, roadmap texts). Each was written by a separate read-only
reviewer given only these principles and the code; the main session spot-checked the decisive claims
(noted at the top of each file).

## Simon's principles

| #   | source                    | principle (his words where quoted)                                                                                   |
|-----|---------------------------|----------------------------------------------------------------------------------------------------------------------|
| P1  | babelfont #90             | code comments state the format rule only -- "the comments are full of implementation details about SFD and fontc and other irrelevancies" |
| P2  | babelfont #90             | symmetric I/O: what is exported to a custom parameter is read back ("The ingress part doesn't seem to be in this PR") |
| P3  | babelfont #95             | data goes in the model's obvious field ("Why not store it in font.version?")                                         |
| P4  | babelfont #93             | no Glyphs custom parameter standing in for a compiler option ("fontc has a --keep-direction flag"); "What are you trying to achieve?" |
| P5  | babelfont #99             | fix it in the tool that owns the problem ("a builder3 issue, not a babelfont one")                                   |
| P6  | babelfont #107            | no filter for a trivial difference ("a one-unit diff in non-integer anchors(!)")                                     |
| P7  | babelfont #105            | kerning goes into the master kerning, not feature code                                                              |
| P8  | babelfont #115            | respect the format's semantics (TrueType flag 0x80 is an ordinary on-curve point)                                    |
| P9  | babelfont #120, #121, #93 | "These weirdly specific FontForge filters are, in general, a bad idea": state the problem, ask whether it is an import problem (then the reader, no flag); a generic filter is named and documented generically |
| P10 | babelfont #118            | our PRs must not conflict with each other ("conflicts with #102")                                                    |
| P11 | babelfont #129            | babelfont is a neutral broker: "Data should always go anything -> babelfont -> anything, and if it can't, then we need to change babelfont" |
| P12 | babelfont #131            | "setting the glyph categories should be enough for the compiler to write a GDEF table": no feature code for what the model states |
| P13 | google/fonts #10490       | the "-Regular-TTF"/"-OTF" .sfd/.vfb files are archival batch conversions of the binaries, not sources: "generate fresh sources using babelfont from the existing Google Fonts binaries"; original .vfb files (annieuseyourtelescope) are fine |

Our derived rule (decided 2026-10-02 after #120/#121): import problem -> reader change without a flag;
generic filter; exporter quirk of the old tool -> a documented source edit in the font repository.

## P13 measured

tools/probes/ttf_sfd_origin/origin.py (results-2026-11-03.tsv): of the 124 "-TTF.sfd" styles our SFD
tables convert (84 repositories), 123 are quadratic like a TrueType import, 112 of them also keep the
binary's TrueType instructions or sit beside a .vfb of the same style; Ultra could not be read. Per
repository: 81 IMPORT on every style (43 published, 38 not), 2 likely (Titillium Web, Tuffy), Ultra
unknown. The unpublished 40 include most of the families the FontForge-specific PRs (#104-#121) were
written for; reland_from_binary.sh lands them from the shipped binaries with the published converter
instead (results in that directory).

The VFB batch shows the same pattern by file name (families-vfb.tsv, 194 styles): 115 styles in 98
repositories convert a "-TTF.vfb" and 5 styles in 2 a "-OTF.vfb" (P13's batch conversions); 74 styles in
35 repositories convert other .vfb files (originals such as annieuseyourtelescope, which Simon called
fine). The five "export rules" of vfb-export-rules (audit B) exist to reproduce what FontLab's exporter
did from those archival files.
