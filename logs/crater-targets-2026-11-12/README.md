# crater-targets-2026-11-12

Inputs and summary of the fontc_crater targets update after google/fonts#11277 and #11303 (`buildVariable: false` in 21 static-only override configs), on top of fontc_crater main's targets.json (99900b5, fonts_repo_sha 5bb28733c).

- `generated.json`: google-fonts-sources d7db2d8 run against google/fonts e77406770 (#11303's merge): `google-fonts-sources <dir> -o generated.json`, with `<dir>/google/fonts` a detached worktree of the google/fonts clone at that commit. `generate.log` is the tool's output (empty).
- `merge.txt`: what `tools/crater_targets.py <99900b5 targets.json> generated.json` reported: 1573 -> 1573 entries, none added, removed or re-pinned. The only change to targets.json is `fonts_repo_sha`, 5bb28733c -> e77406770: crater reads the override configs at that commit.
- `crater-local-tally.txt`: `fontc_crater ci` on the 21 entries whose override config changed (`tools/crater_local.sh`, with those 21 removed from the old file so they count as new), tallied per family by `tools/probes/crater_local/crater_local_tally.py`. fontc 5715ced0 (built with rustc 1.97.1), gftools 0.10.8, fontmake 3.12.2, glyphsLib 6.17.1, ufo2ft 3.11.0, fonttools 4.68.0 (fontc's resources/scripts/requirements.txt).

Result for the 21 entries, 155 targets:

| mode    | result                    | targets |
|---------|---------------------------|---------|
| gftools | identical                 | 36      |
| gftools | fontc fails only          | 30      |
| gftools | fontmake fails only       | 2       |
| gftools | both fail                 | 62      |
| default | fontc fails only          | 1       |
| default | both fail                 | 24      |

In the crater run of 2026-11-09 (results/2026-11-09-170057.json, fontc c0e4f835) the same 21 entries had 25 gftools targets, one per source, and all 25 failed. With the flag crater splits each source into its static instances: 130 gftools targets.

- The 36 identical are instances at a master's location (Amiri, Amiri Quran, Srisakdi, Thasadith: all; Mali, Bai Jamjuree, Chakra Petch, Sarabun, Amaranth roman: some).
- 28 of the 30 where only fontc fails are instances between masters (Bai Jamjuree 6, Chakra Petch 6, Mali 6, Sarabun 10): "Cannot build instance ...: its location ... is not at the location of a master". fontmake interpolates them. The other 2 are Amaranth's italics: "Invalid source glyph 'ellipsis': ... an outline for this location was already defined".
- The 2 where only fontmake fails are Pragati Narrow ("languagesystem deva dflt" has already been specified).
- Both fail: the eight IBM Plex families (fontmake cannot interpolate their instances; IBM Plex Sans KR: glyphsLib ValueError ' 100off'), Istok Web, and Kumar One and Kumar One Outline ("No final targets").
- The default-mode targets build the variable font whatever the config says; they fail as before.
