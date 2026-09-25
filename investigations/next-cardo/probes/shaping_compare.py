#!/usr/bin/env python3
"""Do the release and our build SHAPE marks and kerning the same way?

Question answered: the table gate waves any GPOS difference through as "a legacy kern
modernised into GPOS" whenever both fonts carry lookups, so a build that lost every
mark-to-base lookup still passed it (Cardo-Regular: 30 release lookups vs 20 ours,
diffenator3 reported 45 Hebrew words rendering differently). This shapes a generated
corpus with HarfBuzz (uharfbuzz) in both fonts and compares, per string, the glyphs
(by codepoint when the glyph is encoded, else by name), the absolute position where
each glyph lands, and the total advance.

Corpus, from the codepoints BOTH fonts map:
  base+mark     every base letter (Unicode L*) of each script present x every
                combining mark (Mn/Mc) whose script is that script or Inherited
  base+mark+mark  the same with two marks, for scripts with <= 40 bases (Hebrew)
  pairs         every ordered pair of letters of the same script (kerning), capped
                at the first 120 letters of each script
  kern+mark     every pair above that the RELEASE kerns (its shaped advance differs
                from the plain advance), with a combining mark between the two
                letters (U+0301, U+0308, U+0323 when mapped): tests the kern lookup's
                mark flags (FontForge's flag 0 lets a mark block the pair; a lookup
                with IgnoreMarks kerns across it)
  words         the "word" strings diffenator3 reported in <d3.json>, if given
Each string is shaped with default features, script/direction guessed by HarfBuzz.

Usage:
  shaping_compare.py <shipped.ttf> <built.ttf> [<d3.json>] [--show N] [--only a,b]
  (--only: shape just the named corpora, e.g. --only pairs,kern+mark)
Prints per corpus: strings shaped, strings differing, and the first N differences
(release vs ours as glyph@x,y in visual order, then END@total advance).
Python: /home/fsanches/compartilhado/gftools/venv/bin/python3
"""
import itertools
import json
import sys
import unicodedata

import uharfbuzz as hb
from fontTools.ttLib import TTFont


def script_of(cp):
    try:
        name = unicodedata.name(chr(cp))
    except ValueError:
        return None
    for s in ("HEBREW", "LATIN", "GREEK", "CYRILLIC", "ARABIC", "GOTHIC", "RUNIC",
              "OLD ITALIC", "COPTIC"):
        if name.startswith(s):
            return s
    return None


class Shaper:
    def __init__(self, path):
        self.font = hb.Font(hb.Face(hb.Blob.from_file_path(path)))
        tt = TTFont(path)
        self.order = tt.getGlyphOrder()
        rev = {}
        for cp, n in (tt.getBestCmap() or {}).items():
            rev.setdefault(n, cp)
        self.key = lambda gid: ("U+%04X" % rev[self.order[gid]]) if self.order[gid] in rev \
            else self.order[gid]

    def run(self, text):
        """-> [(glyph, absolute x, absolute y)] + [("END", total advance, 0)].

        What a renderer draws is where each glyph lands, not how the font splits a
        kern between the first glyph's advance and the second glyph's placement:
        FontForge often writes a pair's value on the second glyph (x placement and
        advance) where fontc writes it on the first glyph's advance, and the glyphs
        land on the same pixels. Comparing raw (advance, offset) tuples reported
        such pairs as differences (KellySlab 'AS': release A 627 + S@-13, ours A
        614, both draw S at 614)."""
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        hb.shape(self.font, buf, {})
        out, x = [], 0
        for i, p in zip(buf.glyph_infos, buf.glyph_positions):
            out.append((self.key(i.codepoint), x + p.x_offset, p.y_offset))
            x += p.x_advance
        out.append(("END", x, 0))
        return out


def fmt(run):
    return " ".join("%s@%d,%d" % r for r in run)


def main():
    argv = sys.argv[1:]
    show = 5
    if "--show" in argv:
        i = argv.index("--show")
        show = int(argv[i + 1])
        del argv[i:i + 2]
    only = None
    if "--only" in argv:
        i = argv.index("--only")
        only = set(argv[i + 1].split(","))
        del argv[i:i + 2]
    args = argv
    shipped, built = args[0], args[1]
    d3 = args[2] if len(args) > 2 else None
    S, B = Shaper(shipped), Shaper(built)
    shared = set(TTFont(shipped).getBestCmap()) & set(TTFont(built).getBestCmap())
    bases, marks = {}, {}
    for cp in sorted(shared):
        cat = unicodedata.category(chr(cp))
        sc = script_of(cp)
        if cat.startswith("L") and sc:
            bases.setdefault(sc, []).append(cp)
        elif cat in ("Mn", "Mc"):
            marks.setdefault(sc or "INHERITED", []).append(cp)
    corpora = {"base+mark": [], "base+mark+mark": [], "pairs": [], "kern+mark": [],
               "words": []}
    for sc, bs in bases.items():
        ms = marks.get(sc, []) + marks.get("INHERITED", [])
        for b in bs:
            for m in ms:
                corpora["base+mark"].append(chr(b) + chr(m))
        if len(bs) <= 40:
            own = marks.get(sc, [])
            for b in bs:
                for m1, m2 in itertools.permutations(own, 2):
                    corpora["base+mark+mark"].append(chr(b) + chr(m1) + chr(m2))
        cap = bs[:120]
        for a, b in itertools.product(cap, repeat=2):
            corpora["pairs"].append(chr(a) + chr(b))
    adv = {n: w for n, (w, _) in TTFont(shipped)["hmtx"].metrics.items()}
    cmap_s = TTFont(shipped).getBestCmap()
    between = [m for m in (0x0301, 0x0308, 0x0323) if m in shared]
    for t in corpora["pairs"]:
        run = S.run(t)
        plain = sum(adv[cmap_s[ord(c)]] for c in t)
        if run[-1][1] != plain:
            for m in between:
                corpora["kern+mark"].append(t[0] + chr(m) + t[1])
    if d3:
        d = json.load(open(d3))
        for loc in d.get("locations") or []:
            for lst in (loc.get("words") or {}).values():
                corpora["words"] += [w["word"] for w in lst if "word" in w]
    for name, texts in corpora.items():
        if only is not None and name not in only:
            continue
        diffs = []
        for t in texts:
            a, b = S.run(t), B.run(t)
            if a != b:
                diffs.append((t, a, b))
        print("%s\t%d strings\t%d differ" % (name, len(texts), len(diffs)))
        for t, a, b in diffs[:show]:
            print("   %r (%s)\n     release %s\n     ours    %s"
                  % (t, " ".join("U+%04X" % ord(c) for c in t), fmt(a), fmt(b)))


if __name__ == "__main__":
    main()
