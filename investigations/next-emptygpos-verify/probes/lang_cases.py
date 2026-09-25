#!/usr/bin/env python3
"""Do the specific Varela language cases next-emptygpos cites shape as claimed?

Question: under HarfBuzz (script Latn), does 'fi' ligate under language tr/az/crh in
the release vs a build, and does '!' become exclam.smcp with only `aalt` on under
language sr? Prints glyph names per font per case.

Run: /home/fsanches/compartilhado/gftools/venv/bin/python3 lang_cases.py <release.ttf> <build.ttf> [...more builds]
"""
import sys
import uharfbuzz as hb
from fontTools.ttLib import TTFont

CASES = [("fi", "tr", None), ("fi", "az", None), ("fi", "crh", None), ("fi", "de", None), ("fi", "en", None),
         ("!", "sr", {"aalt": True}), ("!", "en", {"aalt": True}), ("i", "tr", {"smcp": True}), ("i", "en", {"smcp": True})]


def shape(path, text, lang, feats):
    f = hb.Font(hb.Face(open(path, "rb").read()))
    names = TTFont(path).getGlyphOrder()
    b = hb.Buffer()
    b.add_str(text)
    b.direction, b.script, b.language = "ltr", "Latn", lang
    hb.shape(f, b, feats or {})
    return [names[i.codepoint] for i in b.glyph_infos]


for text, lang, feats in CASES:
    print("%-4s %-4s %-16s" % (text, lang, feats or ""), " | ".join(str(shape(p, text, lang, feats)) for p in sys.argv[1:]))
