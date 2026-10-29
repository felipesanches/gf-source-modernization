# vfb_pairing -- does the paired .vfb agree with the release?

`which_vfb.py` converts every `.vfb` a family holds at its recorded commit and scores
each against the shipped font by advance widths (the cheapest signal that a source and
a binary are the same design at the same revision). It checks `tools/pair_vfb.py`'s
pick; it does not change it.

    BF=../babelfont-rs-worktrees/vfb-baseline/target-heights/release/babelfont \
      python3 -I tools/probes/vfb_pairing/which_vfb.py /home/fsanches/compartilhado/tmp/vfb-which-<date> <slug>...

`*` marks the family table's current pick. Read: `advances equal N differ M` over the
glyphs both have.

## 2026-10-29

| family        | result                                                                                                                                                                                             |
|---------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Audiowide     | `-TTF`: 366 of 366 equal; plain and `-OTF`: 0 of 365 (cubic masters at other advances). The rule's pick is right.                                                                                  |
| Aldrich       | `-TTF`: 116 of 116 equal; plain: 0 of 51. Right.                                                                                                                                                   |
| Alfa Slab One | all three candidates: 76 of 226 equal, 150 differ; the release is version 2.000 with 734 glyphs, the commit's sources hold 264. The recorded commit is not the release's source: provenance, not conversion (`baseline` log: 920 rows, 157 advances differ). |
