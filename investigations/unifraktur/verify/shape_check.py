#!/usr/bin/env python3
"""Verifier's own shaping check (independent of sfd-batch5 sweep.py).

Question: with HarfBuzz, does our build shape like the release (glyph names, advances
and offsets) for every cmap'd base followed by each combining mark, and for each
mark alone, in ltr and ttb -- (a) as built (no GPOS) and (b) with the release's
empty GPOS grafted on?

Usage: python3 shape_check.py <release.ttf> <candidate.ttf> [...]
"""
import sys, unicodedata
import uharfbuzz as hb
from fontTools.ttLib import TTFont

def load(p):
    blob = hb.Blob.from_file_path(p); face = hb.Face(blob); font = hb.Font(face)
    names = TTFont(p).getGlyphOrder()
    return font, names

def shape(fh, text, direction):
    font, names = fh
    buf = hb.Buffer(); buf.add_str(text); buf.guess_segment_properties()
    buf.direction = direction
    hb.shape(font, buf, {})
    return tuple((names[i.codepoint], p.x_advance, p.y_advance, p.x_offset, p.y_offset)
                 for i, p in zip(buf.glyph_infos, buf.glyph_positions))

def main():
    rel = sys.argv[1]
    cm = TTFont(rel).getBestCmap()
    marks = [c for c in cm if unicodedata.category(chr(c)) in ('Mn', 'Mc', 'Me')]
    bases = [c for c in cm if unicodedata.category(chr(c))[0] in 'LN']
    texts = [chr(b) + chr(m) for b in bases for m in marks] + [chr(m) for m in marks]
    R = load(rel)
    print('marks', ['U+%04X' % m for m in marks], 'bases', len(bases), 'texts', len(texts))
    for cand in sys.argv[2:]:
        C = load(cand)
        for d in ('ltr', 'ttb'):
            diff = [t for t in texts if shape(R, t, d) != shape(C, t, d)]
            ex = diff[0] if diff else None
            print('%-60s %s differ %5d / %d%s' % (cand.split('/')[-1], d, len(diff), len(texts),
                  '' if ex is None else '  e.g. %r rel=%s ours=%s' % (ex, shape(R, ex, d), shape(C, ex, d))))

main()
