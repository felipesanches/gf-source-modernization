Title: fontlab: read the whole element model

Body:

main converts 45 of 132 VFJ files (FontLab's format examples). Most of the rest fail with "data did not match any variant of untagged enum FontlabElement" (57) or "missing field `layers`" (28).

- Resolve `elementData` that names an element defined on another glyph (ids are font-wide), or that is a composite of other elements.
- Skip elements without geometry, such as stickers, instead of failing.
- Accept fields VFJ omits or writes as floats: glyph `layers`, master tsn/sgn/ffn/psn, capsHeight, component offsets.

Result: 124 of 132 files convert; the 45 that already did give identical output. Three new unit tests. The 11 RoboCJK test failures also occur on main (missing fixture).

Assisted by an AI agent (Claude Opus 5.5)
