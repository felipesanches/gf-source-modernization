# allerta_shared_config

**Question answered:** googlefonts/allerta already holds Allerta (googlefonts/allerta PRs #1
and #2, merged 2026-07-14 and 2026-09-03; google/fonts pins Allerta at bdd9557). The Allerta
Stencil landing adds its source to that repository and edits the shared `sources/config.yaml`
(productionNames, reverseOutlineDirection and decomposeTransformedComponents set to false). Does
that change how Allerta Regular builds, and how close is each build to the shipped font?

    sh check.sh <landed allerta repo> <new commit> <google/fonts clone> <empty scratch dir>

`check.sh` builds Allerta-Regular.glyphs alone with each commit's config (land.py's
gftools-builder, gftools-rust 1e638bd); `compare.py` compares both builds with the shipped
ofl/allerta/Allerta-Regular.ttf.

## Result (result-2026-10-22.txt; the new commit was the Stencil landing on upstream babelfont 5ff5bf04)

| build at                | glyph names as shipped | outlines differ (bounds) | composites | post underline (shipped -76, 51) |
|-------------------------|------------------------|--------------------------|------------|----------------------------------|
| bdd9557 (pinned today)  | no                     | 140 of 215 (2)           | 58         | -100, 50                         |
| Stencil landing         | yes                    | 142 of 217 (3)           | 60         | -100, 50                         |

The config edit changes Allerta Regular's glyf, hmtx and post. Neither build gives the shipped
underline values: the source pinned for Allerta today predates the table gate. Outlines are
compared point by point, so most differences are start points; the bounds column counts
changed shapes.
