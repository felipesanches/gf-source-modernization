#!/usr/bin/env python3
"""Question: of the codepoints a built font lost against its release, how many are the
Glyphs 2 hex-read-as-decimal mistake -- i.e. the glyph that had U+XXXX (XXXX all
decimal digits) sits instead at the decimal number XXXX?

Usage: cmap_hex_as_decimal.py <shipped.ttf> <built.ttf>
"""
import sys
from fontTools.ttLib import TTFont

rel = TTFont(sys.argv[1]).getBestCmap()
ours = TTFont(sys.argv[2]).getBestCmap()
lost = sorted(set(rel) - set(ours))
gained = sorted(set(ours) - set(rel))
hits = [c for c in lost if ("%X" % c).isdigit() and ours.get(int("%X" % c)) == rel[c]]
print("lost %d, gained %d; lost codepoints found at their hex digits read as decimal: %d"
      % (len(lost), len(gained), len(hits)))
print("examples:", " ".join("U+%04X->U+%04X %s" % (c, int("%X" % c), rel[c]) for c in hits[:8]))
print("other lost:", " ".join("U+%04X %s" % (c, rel[c]) for c in lost if c not in hits))
