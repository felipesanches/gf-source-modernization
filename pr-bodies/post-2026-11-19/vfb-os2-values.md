Title: vfb: read the OS/2 and head values the font info states

Body:

The VFB reader currently skips the weight code, PANOSE, vendor and three TrueType-block values (all `todo`), so a converted VFB builds with the compiler's defaults for them. This PR puts them in `custom_ot_values`, which the Glyphs writer already exports:

- usWeightClass from the weight code, as FontLab's export writes it (IBMPlexSerif-Text.vfb: 450; its TrueType block says 400)
- usWidthClass, fsType and head.lowestRecPPEM from the TrueType block
- PANOSE from the font-level entry
- the vendor ID, space-padded when shorter than four characters; a string that cannot be a tag is ignored with a warning

Result: of 50 .vfb files from Google Fonts families, 13 pair with a shipped font. The output now matches it for weight class 13, width class 13, fsType 13, PANOSE 11, vendor ID 11, lowestRecPPEM 6 (main: 0 each); nothing else in the output changes. Two new unit tests.

Assisted by an AI agent (Claude Opus 5.5)
