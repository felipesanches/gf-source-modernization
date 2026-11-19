Title: fontlab: read the whole element model

Body:

The VFJ reader fails on most FontLab files: of 132 .vfj files (FontLab's format examples), main converts 45. The rest stop at "data did not match any variant of untagged enum FontlabElement" (57) or "missing field `layers`" (28).

- `elementData` can be the id of an element defined on another glyph, or a composite gathering more elements; ids are unique font-wide, so a table of them is built up front and references are resolved through it
- elements with no geometry, such as stickers, are skipped instead of failing the parse
- fields VFJ does not always write, or writes as floats, are accepted: glyph `layers`, master tsn/sgn/ffn/psn, capsHeight, component offsets

Test: 124 of the 132 files convert; the 45 that main converts give identical output. Three unit tests; cargo test: 344 pass, plus the 11 RoboCJK tests that fail on main.

Assisted by an AI agent (Claude Opus 5.5)
