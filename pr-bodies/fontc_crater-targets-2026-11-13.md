Title: crater targets: google/fonts at b78877b (buildVariable: false in 35 overrides, 22 corrected pins, 2 corrected configs, skipped.json)

Body:
* google/fonts#11277
* google/fonts#11303
* google/fonts#11312
* google/fonts#11313
* google/fonts#11314
* google/fonts#11317
* google/fonts#11323
* skipped.json: Khula and Nerko One come off (they build now); Charis SIL's reviewed rev follows its new pin; Tiny5, Cairo, Cairo Play and Sawarabi Mincho go on (their sources are generated at build time, so crater reports "missing source").
* Local crater on the 48 affected entries that skipped.json does not list, gftools mode: 70 identical, 56 fontc-only failures (47 are static instances between masters; 5 are Khula, whose `feature pres` block spans two included files).

Assisted by an AI agent (Claude Fable 5.2)
