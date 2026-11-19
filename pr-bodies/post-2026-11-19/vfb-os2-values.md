Title: vfb: read the OS/2 and head values the font info states

Body:

The VFB reader skips the weight code, PANOSE, vendor and the TrueType block's width class, fsType and lowestRecPPEM (all `todo`), so a converted VFB builds with the compiler's defaults for them. This puts them in `custom_ot_values`, which the Glyphs writer already exports:

- usWeightClass from the weight code, which is what FontLab's export writes (IBMPlexSerif-Text.vfb: 450, its TrueType block says 400)
- usWidthClass, fsType and head.lowestRecPPEM from the TrueType block
- PANOSE from the font-level entry
- the vendor ID, padded with spaces when shorter than four characters; a string that cannot be a tag is ignored with a warning

Test: on the 50 .vfb files of the Google Fonts families we convert, the output now matches the shipped fonts for weight class and width class in 13 of 13 files that pair with a release, fsType 13, PANOSE 11, vendor ID 11, lowestRecPPEM 6 (main: 0); nothing else in the output changes. Two unit tests; cargo test: 343 pass, plus the 11 RoboCJK tests that fail on main for the missing designspace.json fixture.

Assisted by an AI agent (Claude Opus 5.5)
