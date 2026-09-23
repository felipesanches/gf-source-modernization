#!/usr/bin/env python3
"""Question: was Nosifer-Regular.ttf generated from a font LOADED from the saved
-TTF.sfd (not from a live GUI session)?  Signals: (1) at every point where the two
releases' glyf coordinates differ, the .sfd prints an exact .5 value and the Nosifer
release holds rint() (half-to-even) of it; (2) gasp version (FF 20110222 sfd.c:1595
does not save gasp_version, so a font loaded from .sfd exports version 0).
Usage: python3 load_from_disk_evidence.py <Nosifer-Regular-TTF.sfd>"""
import re, sys
from fontTools.ttLib import TTFont
N = TTFont("/home/fsanches/compartilhado/google/fonts/ofl/nosifer/Nosifer-Regular.ttf")
C = TTFont("/home/fsanches/compartilhado/google/fonts/ofl/nosifercaps/NosiferCaps-Regular.ttf")
txt = open(sys.argv[1], encoding="latin-1").read()
print("gasp version: Nosifer", N["gasp"].version, "NosiferCaps", C["gasp"].version)
for g in N.getGlyphOrder():
    ga, gb = N["glyf"][g], C["glyf"][g]
    if ga.numberOfContours <= 0: continue
    a, b = list(ga.coordinates), list(gb.coordinates)
    for i, (p, q) in enumerate(zip(a, b)):
        if p != q:
            body = re.search(r"^StartChar: %s\n.*?^EndChar" % re.escape(g), txt, re.M | re.S).group(0)
            halves = sorted(set(re.findall(r"-?\d+\.5(?![0-9])", body)))
            print("%-14s pt%-3d Nosifer %-12s NosiferCaps %-12s  .5 values printed in the .sfd glyph: %s" % (g, i, p, q, halves))
