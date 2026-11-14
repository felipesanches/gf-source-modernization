Title: crater targets: google/fonts at cc39c4c (29 families gain a config, 9 corrected overrides)

Body:
* google/fonts#11326
* google/fonts#11327
* 1573 -> 1602 entries: 29 added (26 upstream configs, 3 override configs), Google Sans Flex re-pinned to v5.000.
* Local crater on the 38 affected entries that skipped.json does not list, gftools mode, 82 targets: 65 identical, 4 differ, 7 fontc-only failures, 6 fail in both.
* fontc-only: BJCree and Hibur Mono (fontc gets `--feature-writer` / `--overlaps-backend` from the config), Geist Serif (.glyphspackage parse error), one Arya instance between masters.
* Both: Coda (glif file names differ in letter case from contents.plist), Nevermind and Xmind (`[ital,wght]` file name not in the stat block), Google Sans Flex, one Arya instance.

Assisted by an AI agent (Claude Fable 5.2)
