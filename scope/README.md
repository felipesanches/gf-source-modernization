# scope -- which families still need a source conversion

`census.py` answers: of the Google Fonts families that do not build from source yet
(gfonts_agents `missing_config` / `no_source`), which have FontForge or FontLab sources to
convert, which only need a build config, which have nothing but binaries -- and which has
this effort already handled? Offline (repo archive + google/fonts checkout).

    /home/fsanches/compartilhado/gftools/venv/bin/python3 scope/census.py > scope/census.tsv

Inputs pinned by the run: gfonts_agents data/gfonts_library_sources.json at 888af17
(2026-09-21), google/fonts at b5efa9c32e8f, the repo archive as of 2026-09-25.

Result of 2026-09-25 (494 families): sfd 8 new + 32 handled; sfd+vfb 75 new + 22 handled;
vfb/vfj 130 new; modern-but-no-config 66 new + 3; binary-only 108; empty 24; no repo 26.
71 new families have .sfd sources, ship static fonts only, and ship fonts carrying
FontForge's FFTM table (so the .sfd is the likely master): the next SFD batch.
9 of the 130 vfb-only families also ship FFTM fonts (a FontForge export of an import).
