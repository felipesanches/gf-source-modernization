# crater-targets-2026-11-08

Inputs and summary of the fontc_crater targets update for google/fonts#11258 (Intel One Mono re-pinned to googlefonts/intel-one-mono 06572f3e, the commit whose build google/fonts shipped), on top of fontc_crater main's targets.json (last changed by googlefonts/fontc_crater#118, a2e66c9).

- `generated.json`: google-fonts-sources d7db2d8 run against google/fonts 5bb28733c (after #11258): `google-fonts-sources <dir> -o generated.json`, with `<dir>/google/fonts` a detached worktree of the google/fonts clone at that commit (its `origin/HEAD` points at `origin/main`). `generate.log` is the tool's output (empty).
- `merge.txt`: what `tools/crater_targets.py <a2e66c9 targets.json> generated.json` reported: 1573 -> 1573 entries, 1 added (googlefonts/intel-one-mono, sources/config.yaml), 1 removed (intel/intel-one-mono 99e2d6c, google/fonts/ofl/intelonemono/config.yaml), no rev change, googlesans-flex kept by hand. The result is the branch's targets.json (crater-targets-2026-11-08).
- No other google/fonts change between bbda7253f and 5bb28733c alters a source entry.
