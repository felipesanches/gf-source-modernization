#!/usr/bin/env python3
"""Is GPOS lookup ORDER the whole of Cardo-Regular's remaining shaping difference?

Question answered: after the converter fixes (runs/p2-proto), Cardo-Regular still
shapes 10 base+mark strings and 7 diffenator3 words differently from the release,
all Hebrew cantillation over vowel points. The release applies FontForge's lookups
in the .sfd's order, which interleaves the anchor (mark-to-base) lookups 0,1,2,5,6,7,
9,10,14,21 with the pair and contextual lookups of the same `mark` feature; our build
gets its mark-to-base lookups from fontc's mark writer, which appends them after
every lookup the FEA defines. This reorders the RELEASE's GPOS the way fontc orders
ours -- every MarkBasePos lookup moved after all other lookups, relative order kept,
feature and contextual lookup indices remapped -- and shapes the differing strings
again: if the reordered release now matches our build, lookup order is the cause.

With --marks-first it instead moves every MarkBasePos lookup BEFORE all others: the
order fontc would produce if babelfont defined a feature's own lookups inside the
feature block after its "# Automatic Code" marker (a possible converter change),
and the full base+mark corpus is compared too.

Usage:
  lookup_order_test.py <release.ttf> <built.ttf> <shaping.txt from shaping_compare.py>
                       [--marks-first]
     (re-shapes every string listed in the shaping file, and the full base+mark corpus)
Prints: per string, release == ours before / after the reorder.
Python: /home/fsanches/compartilhado/gftools/venv/bin/python3
"""
import io
import os
import re
import sys

from fontTools.ttLib import TTFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import shaping_compare as sc  # noqa: E402


def reorder_marks_last(path, out, first=False):
    f = TTFont(path)
    ll = f["GPOS"].table.LookupList.Lookup
    marks = [i for i, lk in enumerate(ll) if lk.LookupType == 4]
    rest = [i for i, lk in enumerate(ll) if lk.LookupType != 4]
    order = marks + rest if first else rest + marks
    new_index = {old: new for new, old in enumerate(order)}
    f["GPOS"].table.LookupList.Lookup = [ll[i] for i in order]
    for fr in f["GPOS"].table.FeatureList.FeatureRecord:
        fr.Feature.LookupListIndex = sorted(new_index[i] for i in fr.Feature.LookupListIndex)
    for lk in f["GPOS"].table.LookupList.Lookup:
        for st in lk.SubTable:
            for rec in getattr(st, "PosLookupRecord", None) or []:
                rec.LookupListIndex = new_index[rec.LookupListIndex]
            for rs in (getattr(st, "ChainPosRuleSet", None) or []):
                for r in rs.ChainPosRule:
                    for rec in r.PosLookupRecord:
                        rec.LookupListIndex = new_index[rec.LookupListIndex]
    f.save(out)
    return order


def main():
    rel, ours, listing = sys.argv[1], sys.argv[2], sys.argv[3]
    first = "--marks-first" in sys.argv
    out = os.path.join("/home/fsanches/compartilhado/sfd-reland-scratch/cardo/sim",
                       "release-" + os.path.basename(rel).replace(
                           ".ttf", "-marks-first.ttf" if first else "-marks-last.ttf"))
    order = reorder_marks_last(rel, out, first)
    print("release lookup order after the move:", order)
    texts = re.findall(r"^   '(.*)' \(", open(listing, encoding="utf-8").read(), re.M)
    R, O, RR = sc.Shaper(rel), sc.Shaper(ours), sc.Shaper(out)
    same_before = same_after = 0
    for t in texts:
        b = R.run(t) == O.run(t)
        a = RR.run(t) == O.run(t)
        same_before += b
        same_after += a
        print("%s\tbefore=%s\tafter=%s" % (" ".join("U+%04X" % ord(c) for c in t),
                                            "same" if b else "DIFF", "same" if a else "DIFF"))
    print("listed strings: %d; equal to ours before the reorder %d, after %d"
          % (len(texts), same_before, same_after))
    if first:
        # the reordered release against the ORIGINAL release, full corpus
        from fontTools.ttLib import TTFont as T
        import unicodedata
        cm = set(T(rel).getBestCmap())
        bases = [c for c in cm if unicodedata.category(chr(c)).startswith("L") and sc.script_of(c)]
        marks = [c for c in cm if unicodedata.category(chr(c)) in ("Mn", "Mc")]
        n = d = 0
        for b in bases:
            for m in marks:
                t = chr(b) + chr(m)
                n += 1
                d += R.run(t) != RR.run(t)
        print("base+mark: release vs release-with-marks-first differ in %d of %d" % (d, n))


if __name__ == "__main__":
    main()
