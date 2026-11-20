Title: vfb: halve the underline thickness with integer division

Body:

VFB stores the middle of the underline and OpenType its top, so the reader adds half the thickness. It currently rounds that half, which is one unit higher than FontLab's export for an odd thickness: -102 and 51 give -76, where the shipped fonts have -77.

This PR halves the thickness with integer division, as FontLab's export does. For an even thickness nothing changes.

Result: of the Google Fonts VFB families, 8 currently convert to an underline one unit above their release (thickness 51 or 75); with this PR all 8 match it. One new unit test.

Assisted by an AI agent (Claude Opus 5.5)
