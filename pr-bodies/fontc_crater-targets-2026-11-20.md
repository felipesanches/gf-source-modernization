Title: crater targets: google/fonts at 869789e (Codystar, Dongle, Englebert, Gowun Batang)

Body:
* google/fonts#11429
* Codystar, Dongle, Englebert and Gowun Batang now build from their googlefonts repositories instead of the google/fonts override configs, which listed .vfb files or a .zip archive. 1602 entries, 4 replaced, no other change.
* This PR also drops those four old configs from skipped.json, since they are no longer in the targets.
* Local crater on the 4 new entries (fontc 9b9c966c, gftools 0.10.8, fontmake 3.12.2): 16 targets in default and gftools modes, all identical.

Assisted by an AI agent (Claude Opus 5.5)
