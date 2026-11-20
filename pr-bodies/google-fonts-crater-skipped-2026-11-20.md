Title: Codystar, Englebert, Gowun Batang, Dongle: reference their googlefonts .glyphs sources

Body:

fontc_crater currently skips these four families: their override config.yaml names FontLab .vfb files or a .zip archive, which no builder reads.

This PR points each METADATA.pb at its new repository under googlefonts, whose .glyphs sources rebuild the fonts Google Fonts ships with gftools-builder and fontc, and removes the override config.yaml (the repository has its own sources/config.yaml). One commit per family, with an upstream_info.md recording what was done:

- Codystar, Englebert: the only published sources are FontLab imports of these fonts (-TTF.vfb), so the fonts were converted.
- Gowun Batang, Dongle: the designer's Glyphs sources (yangheeryu) do not rebuild the release, so the fonts were converted.
- Englebert has two known differences, listed in its README: GSUB lookups numbered or packed differently, with identical shaping; and the head table version, which the release states as 1.010 where the format allows only 1.0.

Assisted by an AI agent (Claude Opus 5.5)
