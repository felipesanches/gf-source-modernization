# crater-targets-2026-10-05

Inputs and summary of googlefonts/fontc_crater#100
(https://github.com/googlefonts/fontc_crater/pull/100), whose first commit is 378754e.

- `generated.json`: google-fonts-sources d7db2d8 run against google/fonts 7085eb89a
  (`google-fonts-sources <dir> -o generated.json`, with `<dir>/google/fonts` a checkout
  of google/fonts main whose `origin/HEAD` points at `origin/main`).
- `merge.txt`: what `tools/crater_targets.py <fontc_crater d9f98fd targets.json>
  generated.json` reported: 1397 -> 1439 entries, 42 added, none removed, no rev change,
  googlesans and googlesans-flex kept by hand.
