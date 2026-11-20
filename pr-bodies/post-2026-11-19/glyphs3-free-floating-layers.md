Title: glyphs3: attach free-floating layers to the default master

Body:

The Glyphs writer currently writes a free-floating layer with its own id as `layerId` and no `associatedMasterId`. In the Glyphs format such a layer is a master layer, so fontc rejects the glyph: `Invalid source glyph 'Odieresis': missing master 'img'`. The VFB reader's `mask` and `img` layers are free-floating, so most converted VFBs currently fail to build.

This PR attaches every free-floating layer to the default master (else the first) when writing a `.glyphs`.

Result: of 40 Google Fonts VFB families, 25 currently fail to build this way; with this PR, 9 of them build again (the other 16 then stop at the VFB's kern feature naming undefined kerning classes, a separate issue). One new unit test.

Assisted by an AI agent (Claude Opus 5.5)
