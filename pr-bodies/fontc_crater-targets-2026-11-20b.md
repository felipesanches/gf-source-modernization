Title: crater targets: google/fonts at 06bfe0d (50 families now build from their googlefonts repositories)

Body:
This PR replaces #130 and keeps its two commits.

* google/fonts#11429, #11433, #11434, #11437
* 50 families now build from their googlefonts repositories: Codystar, Dongle, Englebert and Gowun Batang (#130's commits, which replace their google/fonts override configs and drop those configs from skipped.json), plus 46 more (36 families whose .vfb is an import of the shipped fonts; Beth Ellen, Krona One, Ovo, Pompiere, Short Stack, Sonsie One; Averia Libre, Averia Sans Libre, Averia Serif Libre, Sansation).
* 1602 -> 1648 entries: 50 added, 4 removed, no other change.
* Local crater on the 50 new entries (fontc 9b9c966c, gftools 0.10.8, fontmake 3.12.2): 150 targets in default and gftools modes, all identical.

Assisted by an AI agent (Claude Opus 5.5)
