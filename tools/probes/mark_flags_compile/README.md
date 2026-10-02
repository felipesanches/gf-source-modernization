# mark_flags_compile

Question: does babelfont's --fontforge-mark-lookups turn an SFD anchor lookup's mark attachment class (flag high byte, MarkAttachClasses) and mark filtering set (flag 0x10 + index in the high 16 bits, MarkAttachSets) into a compiled GPOS lookup flag and GDEF classes? No family in the reland corpus uses either, so this synthetic SFD is the only evidence.

Pass (babelfont 5461e295, integration a0eb996e, 2026-10-02): `MarkAttachClassDef {'fatha': 1, 'kasra': 1}`, `MarkGlyphSets [['fatha']]`, lookup 0 (mark-to-base, SFD flag 257) `0x101 None`, lookup 1 (mark-to-mark, SFD flag 65552) `0x10 0`. Without the change the unit test (babelfont filters::fontforgemarklookups) shows the class dropped (`lookupflag RightToLeft;` only), and the old u16 parse turned flag 65552 into 0.

Run: sh tools/probes/mark_flags_compile/check.sh <babelfont release binary>
