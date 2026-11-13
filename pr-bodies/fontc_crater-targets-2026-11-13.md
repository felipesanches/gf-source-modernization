Title: crater targets: google/fonts at 29b4ec6 (buildVariable: false in 35 overrides, 22 corrected pins, 5 corrected configs, skipped.json)

Body:
* google/fonts#11277
* google/fonts#11303
* google/fonts#11312
* google/fonts#11313
* google/fonts#11314
* google/fonts#11317
* google/fonts#11323
* google/fonts#11324
* skipped.json: Khula and Nerko One come off (they build now); Charis SIL's reviewed rev follows its new pin; Tiny5, Cairo, Cairo Play and Sawarabi Mincho go on (their sources are generated at build time, so crater reports "missing source").
* Local crater on the 50 affected entries that skipped.json does not list, gftools mode: 71 identical, 57 fontc-only failures (47 are static instances between masters; 5 are Khula, whose `feature pres` block spans two included files; 1 is Qahiri, fontc#2052).

Assisted by an AI agent (Claude Fable 5.2)
