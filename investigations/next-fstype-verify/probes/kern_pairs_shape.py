#!/usr/bin/env python3
"""kern_pairs_shape.py -- does the build kern every pair exactly as the release does?

Question answered: the table gate accepts the GPOS rows of these styles because "both
fonts position with real lookups" (table_gate.arbitrate_gpos) -- it does not shape the
pairs -- while diffenator3's own kern comparison gives up ("There are N changes, check
manually!"). Shaping EVERY ordered pair of encoded glyphs involved in a PairPos lookup
of the shipped font (first glyph from any PairPos coverage, second from any class-2 /
second-glyph set; all encoded glyphs if the class-2 set is class 0), through HarfBuzz
with default features (kern on), plus the same with cpsp on, how many pairs position
differently (sum of x_advance + x_offset differs)?

Run: $PY kern_pairs_shape.py <shipped.ttf> <built.ttf> [...more pairs]
"""
import sys

import uharfbuzz as hb
from fontTools.ttLib import TTFont


def pair_glyphs(font):
    firsts, seconds, all_second = set(), set(), False
    gpos = font["GPOS"].table
    for lk in gpos.LookupList.Lookup:
        for st in lk.SubTable:
            if lk.LookupType == 9:
                st = st.ExtSubTable
            if getattr(st, "LookupType", lk.LookupType) != 2:
                continue
            firsts |= set(st.Coverage.glyphs)
            if st.Format == 1:
                for ps in st.PairSet:
                    seconds |= {r.SecondGlyph for r in ps.PairValueRecord}
            else:
                seconds |= set(st.ClassDef2.classDefs)
                all_second = True    # class 0 of ClassDef2 = every other glyph
    return firsts, seconds, all_second


def mk(path):
    return hb.Font(hb.Face(hb.Blob.from_file_path(path)))


def run(font, text, feats):
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(font, buf, feats)
    return [(p.x_advance, p.x_offset) for p in buf.glyph_positions]


for sp, bp in zip(sys.argv[1::2], sys.argv[2::2]):
    s = TTFont(sp)
    cmap = s.getBestCmap()
    rev = {}
    for cp, n in sorted(cmap.items()):
        rev.setdefault(n, cp)
    firsts, seconds, all_second = pair_glyphs(s)
    L = sorted(rev[g] for g in firsts if g in rev)
    R = sorted(set(rev.values())) if all_second else sorted(rev[g] for g in seconds if g in rev)
    fs, fb = mk(sp), mk(bp)
    for feats in ({}, {"cpsp": True}):
        n = diff = 0
        ex = []
        for a in L:
            for b in R:
                t = chr(a) + chr(b)
                x, y = run(fs, t, feats), run(fb, t, feats)
                n += 1
                if x != y:
                    diff += 1
                    if len(ex) < 8:
                        ex.append((t, x, y))
        print("%s: features %s: %d pairs shaped, %d position differently %s" % (
            bp.split("/")[-1], feats or "default", n, diff, ex))
