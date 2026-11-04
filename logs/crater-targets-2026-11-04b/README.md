# crater-targets-2026-11-04b

Inputs and summary of the fontc_crater targets update for google/fonts #11234-#11237: Abril Fatface, Carlito and the 80 families converted from their shipped fonts (the 24 archival `.sfd` imports and the 56 `.vfb` imports), on top of the targets of googlefonts/fontc_crater#117 (branch crater-targets-2026-11-04, https://github.com/felipesanches/fontc_crater/commit/76288e8; fontc_crater main's targets.json has not changed since 2c7b075).

- `generated.json`: google-fonts-sources d7db2d8 run against google/fonts bbda7253f (after #11237): `google-fonts-sources <dir> -o generated.json`, with `<dir>/google/fonts` a detached worktree of the google/fonts clone at that commit (its `origin/HEAD` points at `origin/main`). `generate.log` is the tool's output (empty).
- `merge.txt`: what `tools/crater_targets.py <76288e8 targets.json> generated.json` reported: 1491 -> 1573 entries, 82 added, none removed, no rev change, googlesans-flex kept by hand. The result is the branch's targets.json.
- Every added entry is at its repository's default-branch head, except Abril Fatface at 9d1486e, the commit google/fonts records, one commit before master's head (the hardened build workflow).
- Crater on the 82 added entries before the PR: logs/crater-local-2026-11-04b (226 of 226).
