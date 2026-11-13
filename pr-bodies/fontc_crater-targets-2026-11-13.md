Title: crater targets: google/fonts at 3e56677 (corrected pins, buildVariable: false overrides)

Body:
* google/fonts#11277
* google/fonts#11303
* google/fonts#11312, google/fonts#11313, google/fonts#11314: corrected pins. 14 entries change rev, 7 move (fork or override config), Playfair Display SC gets its own: 1573 -> 1574.
* google/fonts#11317: no entry changes; crater reads the override configs at fonts_repo_sha.
* Local crater on the 36 affected entries, gftools mode: 55 identical, 50 fontc-only failures (46 are static instances between masters).

Assisted by an AI agent (Claude Fable 5.2)
