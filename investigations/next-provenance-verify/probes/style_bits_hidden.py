#!/usr/bin/env python3
"""Which functional OS/2 / head style bits differ between each release and our build,
although sfd-batch5/tools/table_gate.py ACCEPTS the whole fields (OS/2.fs_selection:
"USE_TYPO_METRICS is set by the build"; head.mac_style: "derived from the style")?

Question answered, per style of unit "provenance": release vs build OS/2 version,
fsSelection bits (ITALIC 0, BOLD 5, REGULAR 6, USE_TYPO_METRICS 7), head.macStyle, and the
line-spacing metrics a USE_TYPO_METRICS-honouring app uses (typo asc/desc/gap) versus the
ones it uses without it (win asc/desc; hhea). FontForge (tottf.c at eb711fd7, lines
3278-3291) sets bit 7 only when the OS/2 version it writes is >= 4, and derives macStyle
italic from the name modifiers "Ital|Obli|Slanted|Kurs|It" (macbinary.c _MacStyleCode).

Run: python3 style_bits_hidden.py   (reads the verifier's scratch builds pv-v3 / w2)
"""
import glob
from fontTools.ttLib import TTFont

S = "/home/fsanches/compartilhado/sfd-reland-scratch/provenance-verify/baseline"
GF = "/home/fsanches/compartilhado/google/fonts"
CASES = [("Lohit-Bengali", "ofl/lohitbengali/Lohit-Bengali.ttf", "pv-v3"),
         ("Lohit-Tamil", "ofl/lohittamil/Lohit-Tamil.ttf", "pv-v3")] + [
         (s, "ofl/thabit/%s.ttf" % s, "w2-workarounds") for s in
         ("Thabit", "Thabit-Bold", "Thabit-Oblique", "Thabit-BoldOblique")]
BITS = {0: "ITALIC", 5: "BOLD", 6: "REGULAR", 7: "USE_TYPO_METRICS", 9: "OBLIQUE"}


def desc(f):
    o = f["OS/2"]
    bits = [n for b, n in BITS.items() if o.fsSelection & (1 << b)]
    return "OS/2 v%d fsSelection %s macStyle %d | typo %d/%d/%d win %d/%d hhea %d/%d/%d" % (
        o.version, "+".join(bits), f["head"].macStyle, o.sTypoAscender, o.sTypoDescender,
        o.sTypoLineGap, o.usWinAscent, o.usWinDescent, f["hhea"].ascent, f["hhea"].descent,
        f["hhea"].lineGap)


for style, rel, tag in CASES:
    built = glob.glob("%s/%s-%s/fonts/ttf/*.ttf" % (S, style, tag))[0]
    print("%-19s release %s" % (style, desc(TTFont("%s/%s" % (GF, rel)))))
    print("%-19s ours    %s" % ("", desc(TTFont(built))))
