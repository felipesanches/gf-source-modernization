# FontLab readers on 2026-11-19: what of our VFB/VFJ work is still not in babelfont-rs main

Question answered: after Simon Cozens's FontLab work of 2026-11-16 to 2026-11-18 (babelfont-rs main
f253aa84, vfbreader 0.1.7), which items of the 2026-11-17 report (gfonts-ai-usage-report
25-fontlab-upstream-2026-11-17) does main still lack, and do the rebased branches add exactly those?

Builds (rustc 1.97.1; main needs 1.96 or later), each in its own target directory:

| label | branch (babelfont-rs-worktrees)           | revision |
|-------|-------------------------------------------|----------|
| main  | upstream-main-2026-11-19 (detached)       | f253aa84 |
| ours  | vfb-integration-2026-11-17 (the report's) | e292cbec |
| os2   | vfb-os2-values-2026-11-19                 | 849c87c4 |
| vfj   | vfj-elements-2026-11-19                   | f6e78338 |

## Scripts

| script             | question it answers                                                                                                        | command                                                                               |
|--------------------|----------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------|
| convert_ab.sh      | do two builds convert every .vfb (EXT=vfj: .vfj) of a corpus, and identically?                                             | `[C=<corpus>] [EXT=vfj] [FLAGS=...] sh convert_ab.sh <outdir> <label>=<babelfont>...` |
| compare_topics.py  | in which topics (names, metrics, kerning, groups, anchors, glyph names, outlines, features) do two builds' outputs differ? | `python3 -I compare_topics.py <outdir> <a> <b> [--detail <topic>]`                    |
| compare_release.py | where two builds differ, which one states what the shipped font has?                                                       | `python3 -I compare_release.py <outdir> <a> <b> [--show <field>]`                     |

Corpora: the 50 unique .vfb files of the VFB landing clones (default `C`), and the 132 unique .vfj
files under `vfj-research` (FontLab's format examples plus one minimal file).

## Results

**The report's VFB items against main** (`vfb-ours-main.tsv`, `topics-ours-main.txt`, `release-ours-main.txt`;
13 of the 50 files pair with a shipped font through families-vfb.tsv or families-binary.tsv):

| item in the report                                               | in main now? | evidence                                                                                         |
|------------------------------------------------------------------|--------------|--------------------------------------------------------------------------------------------------|
| anchors                                                          | yes          | 0 of 50 files differ                                                                             |
| glyph names                                                      | yes          | 0 of 50 files differ                                                                             |
| kerning and kerning classes                                      | yes, more    | main writes the class kerning as groups and pairs; ours left part of it in the feature code      |
| names                                                            | yes          | family, style, designer, URLs agree; description and license disagree both ways (no reader rule) |
| x-height, cap height                                             | yes          | equal; main also takes ascender and descender from PostScript Info                               |
| underline as the top of the stroke                               | yes          | main applies it                                                                                  |
| sub/superscript, strikeout, metrics                              | yes          | per master in main, font-wide in ours: same values                                               |
| weight and width class, fsType, PANOSE, vendor ID, lowestRecPPEM | **no**       | main states none; ours matches the release in 13, 13, 13, 11, 11, 6 files                        |

**The VFB PR** (`vfb-main-os2.tsv`, `release-main-os2.txt`, `topics-main-os2.txt`, with
`FLAGS=--add-instance-per-master`): os2 matches the release in weight class 13, width class 13,
fsType 13, PANOSE 11, vendor ID 11, lowestRecPPEM 6 files (main: 0). Nothing else changes: only the
fsType, PANOSE, lowestRecPPEM and vendorID values differ from main's output. The files where neither
matches have releases edited after the .vfb (e.g. Libre Caslon Display: vendor IMPA, the .vfb pyrs).

**The VFJ PR** (`vfj-main-elements.tsv`, `vfj-main-errors.txt`): main converts 45 of 132 files, the
branch 124. Main's failures: elements matching no FontlabElement variant (57), glyphs with no `layers`
(28), axis mappings (2). The 45 that main converts are identical with the branch (ignoring the run
date and random ids). Our "axis default from the default master" commit no longer changes any output
(main's 1d100a34 covers it) and our layer-to-master binding is in main: both dropped. 8 files fail with
both builds (with the branch: "NoDefaultMaster" when saving).

Tests: `cargo +1.97.1 test -p babelfont --features cli`: main 341 passed, 11 failed (RoboCJK
fixture designspace.json missing); os2 343 passed, vfj 344 passed, the same 11 failing.
