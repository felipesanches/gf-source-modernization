#!/usr/bin/env python3
"""Does a candidate build shape like the release under HarfBuzz?

Question: after a layout change (the FontForge GPOS shell, or none), which shaped runs
still put ink somewhere other than the release does, and in which direction?

Signal read: HarfBuzz output accumulated to ink positions, exactly as
sfd-batch5/tools/probes/gdef_mark_vs_base/sweep.py (at cbdf708) does -- per glyph
(glyph NAME, cluster, pen_x + x_offset, pen_y + y_offset) plus the final pen -- over
4 directions x 4 buffer-flag sets x 3 kern settings (48 runs per text). Glyph names,
not ids, so a different glyph order is not a difference. Two fonts that agree on
every tuple draw the same ink in the same place.

Corpus = sweep.py's own corpus of the RELEASE (its GPOS glyph pairs bare / with one
and two marks between, every combining mark alone / after H / doubled, every
codepoint alone and after H) PLUS what sweep.py does not reach:
  kern-bare / kern-1mark   every pair of the release's legacy `kern` table (format 0),
                           bare and with each combining mark between the two members
                           (the legacy table is applied with IgnoreMarks)
  base-mark                every cmap'd letter or digit followed by each combining mark
                           the font encodes (HarfBuzz's fallback mark positioning acts
                           here, and only when the font has no GPOS)

Run:
    /home/fsanches/compartilhado/gftools/venv/bin/python3 shape_compare.py \
        <release.ttf> <candidate.ttf> [<candidate2.ttf> ...]
Prints, per candidate: total runs, differing runs, split horizontal (ltr+rtl) and
vertical (ttb+btt), per corpus label, and the first horizontal difference in full.
"""
import collections
import importlib.util
import itertools
import sys
import unicodedata

from fontTools.ttLib import TTFont

SWEEP = "/home/fsanches/compartilhado/sfd-batch5/tools/probes/gdef_mark_vs_base/sweep.py"
_spec = importlib.util.spec_from_file_location("sweep", SWEEP)
sweep = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sweep)


def corpus(release):
    out = list(sweep.corpus(release))
    f = TTFont(release)
    cmap = f.getBestCmap()
    rev = {}
    for c, g in sorted(cmap.items()):
        rev.setdefault(g, c)
    marks = [chr(c) for c in sorted(cmap)
             if unicodedata.category(chr(c)) in ("Mn", "Mc", "Me")]
    if "kern" in f:
        for st in f["kern"].kernTables:
            for (l, r) in getattr(st, "kernTable", {}):
                a, b = rev.get(l), rev.get(r)
                if a is None or b is None:
                    continue
                out.append(("kern-bare", chr(a) + chr(b)))
                for m in marks:
                    out.append(("kern-1mark", chr(a) + m + chr(b)))
    for c in sorted(cmap):
        if unicodedata.category(chr(c))[0] in "LN":
            for m in marks:
                out.append(("base-mark", chr(c) + m))
    return out


def compare(release, cand, cases):
    fa, fb = sweep.hbfont(release), sweep.hbfont(cand)
    na, nb = sweep.glyph_names(release), sweep.glyph_names(cand)
    total = 0
    diffs = []
    for (label, text), direction, (fname, flags), (ftname, feats) in itertools.product(
            cases, sweep.DIRECTIONS, sweep.FLAGS, sweep.FEATURES):
        total += 1
        a = sweep.run(fa, text, direction, flags, feats, na)
        b = sweep.run(fb, text, direction, flags, feats, nb)
        if a != b:
            diffs.append((label, text, direction, fname, ftname, a, b))
    return total, diffs


def main():
    release, cands = sys.argv[1], sys.argv[2:]
    cases = corpus(release)
    labels = collections.Counter(l for l, _ in cases)
    print("release %s: %d texts (%s)" % (release.rsplit("/", 1)[-1], len(cases),
                                        ", ".join("%s=%d" % kv for kv in sorted(labels.items()))))
    rc = 0
    for cand in cands:
        total, diffs = compare(release, cand, cases)
        hor = [d for d in diffs if d[2] in ("ltr", "rtl")]
        ver = [d for d in diffs if d[2] in ("ttb", "btt")]
        texts_h = {(d[0], d[1]) for d in hor}
        print("%s: %d runs, %d differ (horizontal %d in %d texts; vertical %d)"
              % (cand.rsplit("/", 1)[-1], total, len(diffs), len(hor), len(texts_h), len(ver)))
        by = collections.Counter(d[0] for d in hor)
        for lab, n in sorted(by.items()):
            print("    horizontal %-14s %6d runs" % (lab, n))
        if hor:
            rc = 1
            d = hor[0]
            print("    first: %s %r dir=%s flags=%s feat=%s" % d[:5])
            print("      release: %s" % (d[5],))
            print("      cand   : %s" % (d[6],))
    return rc


if __name__ == "__main__":
    sys.exit(main())
