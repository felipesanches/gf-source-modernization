#!/usr/bin/env python3
"""Would the two rows Thabit keeps close if the gate treated them as it treats FFTM?

Question answered: after every build step and converter rule, each Thabit style keeps two
table rows: `PfEd: whole-table difference` and `head.font_direction_hint [0, 2]`.
- PfEd is FontForge's private table (in these releases: the GSUB/GPOS lookup, subtable
  and anchor-class NAMES, so a round trip through FontForge keeps them). No shaper or
  rasterizer reads it; the gate already accepts FontForge's other private table, FFTM.
- head.fontDirectionHint is deprecated ("Set to 2", OpenType head spec). FontForge 2008
  writes 0 when a font has both left-to-right and right-to-left glyphs, -2 when only
  right-to-left, else 2 (tottf.c sethead: `if ( lr && rl ) head->dirhint = 0;`); a Glyphs
  source cannot state it and fontc writes 2.
This runs sfd-batch5/tools/table_gate.py unchanged except that ACCEPTED gains
'PfEd' (whole table) and head.font_direction_hint, and prints its verdict.

Usage: table_gate_ff_private.py <d3.json> --fonts <shipped.ttf> <built.ttf>
"""
import sys

sys.path.insert(0, "/home/fsanches/compartilhado/sfd-batch5/tools")
import table_gate  # noqa: E402

table_gate.ACCEPTED["PfEd"] = None
table_gate.ACCEPTED["head"]["font_direction_hint"] = (
    "deprecated field (OpenType: set to 2); FontForge writes 0 for a font with both LTR "
    "and RTL glyphs (tottf.c sethead)")

if __name__ == "__main__":
    sys.argv = [sys.argv[0]] + sys.argv[1:]
    table_gate.main()
