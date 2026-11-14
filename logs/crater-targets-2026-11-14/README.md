# crater-targets-2026-11-14

Inputs and summary of the fontc_crater targets branch crater-targets-2026-11-14, after google/fonts#11326 (source metadata of 43 recently added or updated families) and #11327 (9 override configs pointed at the sources that shipped).

- `generated.json`: google-fonts-sources 0.11.2 run against [google/fonts cc39c4c2](https://github.com/google/fonts/tree/cc39c4c2c): `google-fonts-sources <dir> -o generated.json`, with `<dir>/google/fonts` a detached worktree at that commit.
- `merge.txt`: what `tools/crater_targets.py <main's targets.json> generated.json` reported: 1573 -> 1602 entries; 29 added, none removed, 1 re-pinned (Google Sans Flex).
- `crater-local-tally.txt`: `fontc_crater ci` (`tools/crater_local.sh`) on the 39 changed entries: the 30 added or re-pinned ones, plus the 9 overrides of #11327, removed from the old file so they count as new. The output directory held the branch's `results/skipped.json`, as crater's CI does, so Dai Banna SIL was not built. Tallied by `tools/probes/crater_local/crater_local_tally.py`. fontc 5715ced0 (rustc 1.97.1), gftools 0.10.8, fontmake 3.12.2, glyphsLib 6.17.1, ufo2ft 3.11.0, fonttools 4.68.0.
- `crater-local-union.txt`: both result files together, by `tools/probes/crater_local/crater_local_union.py --skipped <skipped.json> <main run> <Gayathri run>`.

The main run reported Gayathri as "missing source 'sources/Gayathri-Bold.ufo'" and left no clone in its cache; the pinned commit has the three UFOs. A second run on that entry alone cloned and built it, so the first was a failed fetch.

Result for the 38 entries crater builds, 160 targets:

| mode    | result              | targets |
|---------|---------------------|---------|
| gftools | identical           | 65      |
| gftools | differ              | 4       |
| gftools | fontc fails only    | 7       |
| gftools | fontmake fails only | 0       |
| gftools | both fail           | 6       |
| default | identical           | 66      |
| default | differ              | 5       |
| default | fontc fails only    | 3       |
| default | fontmake fails only | 1       |
| default | both fail           | 3       |

- fontc fails only (gftools mode), 7: BJCree's 4 statics (the fontc command line gets `--feature-writer`, which fontc does not accept), Hibur Mono (same with `--overlaps-backend`), Geist Serif (fontc cannot parse the .glyphspackage), one Arya instance at no master's location.
- Both fail (gftools mode), 6: Coda's two UFOs (contents.plist names glif files with capitals the repository stores in lowercase), Nevermind and Xmind (gftools names the font `[ital,wght]`, which the config's stat block does not list), Google Sans Flex (no output), one Arya instance (`instance_ufos/Arya-Regular.ufo.json not found`).
- Default mode, fontc only: Geist Serif, Nevermind and Xmind (`Invalid tag 'XMIND'`). fontmake only: Google Sans Flex (incompatible glyphs). Both: Coda's two UFOs, Tangerine ('Euro' is not interpolatable; its statics build in gftools mode).
- Differ: Gayathri (3 in each mode), M PLUS Code Latin (1 in each mode), BJCree (default mode).
- The other 27 entries are identical in every target, among them Cabin, Cambay, Sigmar and Isometra (overrides) and Castoro Titling, Cousine, Tinos, Redaction and Scoutie Sans (upstream configs).
