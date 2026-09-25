#!/usr/bin/env python3
"""Two harness sweeps of one pairing table, side by side: table rows AND rendering diffs.

Question answered: does a converter change (or a recipe flag) change any style's result?
tools/baseline.sh reports only table-gate rows; the rendering diff diffenator3 also wrote
(its `locations` section, which neither baseline.sh nor land.py gates) is in each run's
scratch d3.json. For every style this prints, for sweep A and sweep B: verdict, blocking
rows, and diffenator3 glyph / word difference counts, and flags every style whose numbers
differ.

Usage:
  sweep_summary.py <OUT dir A> <scratch root A> <TAG A> <OUT dir B> <scratch root B> <TAG B>
(scratch dir of a style = <scratch root>/baseline/<Style>-<TAG>)
"""
import glob
import json
import os
import sys


def d3_counts(path):
    try:
        d = json.load(open(path))
    except Exception:
        return None
    g = sum(len(L.get("glyphs") or []) for L in d.get("locations") or [])
    w = sum(len(x) for L in d.get("locations") or [] for x in (L.get("words") or {}).values())
    return g, w


def sweep(out, scratch, tag):
    res = {}
    for tsv in glob.glob(os.path.join(out, "*.tsv")):
        row = open(tsv).read().rstrip("\n").split("\t")
        if len(row) < 4:
            continue
        style = row[1]
        res[style] = (row[2], row[3], d3_counts(os.path.join(scratch, "baseline", "%s-%s" % (style, tag), "d3.json")))
    return res


def main(a_out, a_scr, a_tag, b_out, b_scr, b_tag):
    A, B = sweep(a_out, a_scr, a_tag), sweep(b_out, b_scr, b_tag)
    changed = 0
    for style in sorted(set(A) | set(B)):
        a, b = A.get(style), B.get(style)
        mark = "" if a == b else "  <-- differs"
        changed += a != b
        print("%-28s A %-40s B %-40s%s" % (style, a, b, mark))
    print("%d of %d styles differ" % (changed, len(set(A) | set(B))))


if __name__ == "__main__":
    main(*sys.argv[1:7])
