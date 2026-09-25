#!/usr/bin/env python3
"""Independent re-measurement: which ordered two-character strings shape differently?

Question: for a release font and a candidate build of the same style, over every
ordered pair (a, b) of the release's cmap'd codepoints >= U+0020, does HarfBuzz
give the same glyph names, x/y advances and x/y offsets?  Written from scratch
(does NOT import sfd-batch5 sweep.py) so it can check next-emptygpos's
pair_matrix.py counts.

Signal read: uharfbuzz shape(), direction ltr, script Latn, language "en",
default features, default buffer flags. Glyph identity is compared by NAME
(post table / glyph order), not gid. A pair "differs" when the tuple
[(name, x_advance, y_advance, x_offset, y_offset) ...] differs. Because advances are
compared raw, a pair whose ink lands in the same place but whose advance split
differs also counts; --ink compares absolute ink x positions (pen + x_offset,
y_offset) plus the final pen instead, which is what a reader sees.

Groups: soft-hyphen (either char U+00AD), mark (either char general category
Mn/Mc/Me), other; 'other' is further broken down by first character.

Run:
  /home/fsanches/compartilhado/gftools/venv/bin/python3 pairs_hb.py <release.ttf> <candidate.ttf> [--ink] [--show N] [--dir ltr|ttb]
"""
import collections
import sys
import unicodedata

import uharfbuzz as hb
from fontTools.ttLib import TTFont


def load(path):
    data = open(path, "rb").read()
    face = hb.Face(data)
    font = hb.Font(face)
    names = TTFont(path).getGlyphOrder()
    return font, names


def shape(font, names, text, direction, ink):
    buf = hb.Buffer()
    buf.add_str(text)
    buf.direction = direction
    if direction == "ltr":
        buf.script = "Latn"
    else:
        buf.script = "Latn"
    buf.language = "en"
    hb.shape(font, buf, {})
    out = []
    pen_x = pen_y = 0
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        if ink:
            out.append((names[info.codepoint], pen_x + pos.x_offset, pen_y + pos.y_offset))
        else:
            out.append((names[info.codepoint], pos.x_advance, pos.y_advance, pos.x_offset, pos.y_offset))
        pen_x += pos.x_advance
        pen_y += pos.y_advance
    if ink:
        out.append(("<end>", pen_x, pen_y))
    return tuple(out)


def group(t):
    if "\xad" in t:
        return "soft-hyphen"
    if any(unicodedata.category(c) in ("Mn", "Mc", "Me") for c in t):
        return "mark"
    return "other"


def main():
    argv = sys.argv[1:]
    ink = "--ink" in argv
    show = 6
    direction = "ltr"
    if "--show" in argv:
        show = int(argv[argv.index("--show") + 1])
    if "--dir" in argv:
        direction = argv[argv.index("--dir") + 1]
    pos = [a for i, a in enumerate(argv) if not a.startswith("--") and (i == 0 or argv[i - 1] not in ("--show", "--dir"))]
    rel, cand = pos[:2]
    cps = [c for c in sorted(TTFont(rel).getBestCmap()) if c >= 0x20]
    fa, na = load(rel)
    fb, nb = load(cand)
    diffs = []
    for a in cps:
        for b in cps:
            t = chr(a) + chr(b)
            ra = shape(fa, na, t, direction, ink)
            rb = shape(fb, nb, t, direction, ink)
            if ra != rb:
                diffs.append((t, ra, rb))
    by = collections.Counter(group(t) for t, _, _ in diffs)
    print("%s vs %s [%s, %s]: %d ordered pairs, %d differ %s" % (
        rel.rsplit("/", 1)[-1], cand.rsplit("/", 1)[-1], direction,
        "ink" if ink else "raw", len(cps) ** 2, len(diffs), dict(sorted(by.items()))))
    firsts = collections.Counter(t[0] for t, _, _ in diffs if group(t) == "other")
    if firsts:
        print("  other by first char: " + ", ".join(
            "%s(U+%04X)=%d" % (c, ord(c), n) for c, n in firsts.most_common(40)))
    seconds = collections.Counter(t[1] for t, _, _ in diffs if group(t) == "other")
    if seconds:
        print("  other by second char: " + ", ".join(
            "%s(U+%04X)=%d" % (c, ord(c), n) for c, n in seconds.most_common(15)))
    marks = collections.Counter(c for t, _, _ in diffs if group(t) == "mark" for c in t
                                if unicodedata.category(c) in ("Mn", "Mc", "Me"))
    if marks:
        print("  marks involved: " + ", ".join("U+%04X=%d" % (ord(c), n) for c, n in marks.most_common()))
    for g in ("other", "soft-hyphen", "mark"):
        for t, ra, rb in [d for d in diffs if group(d[0]) == g][:show]:
            print("  %-11s %s\n     release %s\n     cand    %s" % (
                g, " ".join("U+%04X" % ord(c) for c in t), ra, rb))


if __name__ == "__main__":
    main()
