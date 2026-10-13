# hb_synthesized_classes

Question answered: in a font without GDEF glyph classes, which Unicode general categories does
HarfBuzz take for marks? (The table gate's model of a GDEF-less release said Mn, Mc and Me; the
functional gate's said Mn.)

    python3 probe.py        (needs fontTools and uharfbuzz)

It builds a font without GDEF that kerns `a a` by -100 under IgnoreMarks and shapes `a` + X +
`a` for one character of each category: the kern applies across X only if HarfBuzz synthesised
X as a mark. Result (`result.txt`, uharfbuzz 0.53.3): U+0301 (Mn) a mark; U+20DD and U+0488 (Me)
and U+0903 (Mc) bases. U+034F (Mn, default-ignorable) lets the kern through too, but HarfBuzz
skips default-ignorables while matching whatever their class; its source classes them as bases.
