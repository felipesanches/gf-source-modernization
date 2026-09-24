#!/usr/bin/env python3
"""Message filter: replace each commit message, looked up by its subject."""
import sys

A = "Assisted by an AI agent (Claude Opus 5.5)"

MSGS = {
    "fontforge: decode a quoted glyph name, and trim before unquoting": """\
A quoted glyph name is modified UTF-7, like the subtable, lookup, class and
nameid strings the convertor already decodes. Trim trailing whitespace
before unquoting.""",
    "Do not emit a lookup as a feature prefix when only aalt uses it": """\
Its rules are already inlined into aalt, so the prefix was a lookup nothing
referenced. A lookup that a chain context calls by name keeps its definition.""",
    "Add a filter to drop FontForge AltUni alternate codepoints": """\
--drop-alternate-unicodes keeps each glyph's Encoding codepoint and drops the
plain AltUni2 alternates, which FontForge's TTF export did not emit.
Variation sequences are untouched; a glyph is never left unmapped.""",
    "Add a filter to reverse every closed contour": """\
--reverse-path-direction is the counterpart to --correct-path-direction for a
font whose mixed contour directions are meant to be kept.""",
    "Add a filter to keep the glyph names the source states": """\
--keep-source-glyph-names sets the Glyphs custom parameter "Don't use
Production Names" in the source; main.rs honours it when babelfont compiles.""",
    "Add a filter to keep the advances the source states": """\
--keep-source-advances records an uncategorised glyph with a non-zero advance
as a base, so a GlyphData lookup cannot zero it as a mark. Run
--infer-mark-category first.""",
    "Add a filter to read a FontForge component transform as what it means": """\
--snap-component-transforms reads a scale within 1.5 F2Dot14 steps of an
integer as that integer, and an offset within 0.1 unit as that unit.""",
    "Resolve a half-unit component offset the way FontForge's exporter does": """\
--snap-component-transforms now rounds every component offset with rint
(ties to even), as FontForge's dumpcomposite() does.""",
    "Add an opt-in filter for FontForge's underline-position offset": """\
--fontforge-underline-position converts UnderlinePosition (the centre) to
post.underlinePosition (the top) with dumppost()'s pre-2019 rule,
position - thickness/2.""",
    "Add an opt-in filter for FontForge's OS/2 sub/superscript defaults": """\
--fontforge-os2-defaults fills the sub/superscript and strikeout metrics a
source does not state, as SFDefaultOS2SubSuper in tottf.c does.""",
    "Fill PANOSE too, from FontForge's SFDefaultOS2Simple": """\
Bytes 0 and 3 are fixed; byte 2 comes from the weight name, as in
OS2WeightCheck.""",
    "Fill the x-height and cap height the way FontForge's exporter does": """\
--fontforge-os2-defaults also fills them when the source states neither, as
SFStandardHeight in splinefont.c does.""",
    "Add a filter for the height mean of a FontForge built before 2012-05-14": """\
Until FontForge 4d34d21ef866, SFStandardHeight divided the sum of the distinct
round tops by the glyph count. --fontforge-height-glyph-count-mean fills the
heights that way; run it before --fontforge-os2-defaults.""",
}

msg = sys.stdin.read()
subject = msg.split("\n", 1)[0].strip()
if subject not in MSGS:
    sys.exit(f"no message for subject: {subject!r}")
sys.stdout.write(f"{subject}\n\n{MSGS[subject]}\n\n{A}\n")
