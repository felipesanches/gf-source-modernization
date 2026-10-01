#!/usr/bin/env python3
"""Question answered: between two re-land runs, which styles did a converter or plan change
fix, which did it break, and what still fails -- per style and per functional-gate check.

Reads logs/reland-<old>/*.log and logs/reland-<new>/*.log with reland_triage.parse and
prints: verdict changes per style (FAIL->PASS, PASS->FAIL), checks gained and lost per
style, and per-check totals in both runs. Repos missing from either run are listed, not
compared. Writes logs/reland-<new>/compare-<old>.tsv (repo, style, old checks, new checks).

Usage: compare_runs.py <old tag> <new tag>
"""
import collections
import glob
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from reland_triage import CHECKS, W, parse  # noqa: E402


def load(tag):
    d = os.path.join(W, "logs", "reland-" + tag)
    styles, fails = {}, collections.defaultdict(set)
    for log in sorted(glob.glob(os.path.join(d, "*.log"))):
        r = parse(log)
        if not isinstance(r, tuple):
            for row in r:
                styles[(row["repo"], "-")] = ("-", "LANDING")
            continue
        rows, st = r
        for repo, style, table, fverdict in st:
            styles[(repo, style)] = (table, fverdict)
        for row in rows:
            if row["check"] in CHECKS:
                fails[(row["repo"], row["style"])].add(row["check"])
    return styles, fails


def main():
    old, new = sys.argv[1], sys.argv[2]
    so, fo = load(old)
    sn, fn = load(new)
    ro = {k[0] for k in so}
    rn = {k[0] for k in sn}
    if ro - rn:
        print("only in %s: %s" % (old, " ".join(sorted(ro - rn))))
    if rn - ro:
        print("only in %s: %s" % (new, " ".join(sorted(rn - ro))))
    keys = sorted(k for k in sn if k[0] in ro)
    fixed, broke, changed = [], [], []
    for k in keys:
        a, b = so.get(k, ("?", "?")), sn[k]
        ca, cb = fo.get(k, set()), fn.get(k, set())
        if a[1] != "PASS" and b[1] == "PASS":
            fixed.append(k)
        elif a[1] == "PASS" and b[1] != "PASS":
            broke.append(k)
        elif ca != cb:
            changed.append(k)
    out = os.path.join(W, "logs", "reland-" + new, "compare-%s.tsv" % old)
    with open(out, "w") as fh:
        fh.write("repo\tstyle\told_verdict\tnew_verdict\told_table\tnew_table\told_fails\tnew_fails\n")
        for k in keys:
            a, b = so.get(k, ("?", "?")), sn[k]
            fh.write("\t".join([k[0], k[1], a[1], b[1], a[0], b[0],
                                "+".join(sorted(fo.get(k, ()))) or "-",
                                "+".join(sorted(fn.get(k, ()))) or "-"]) + "\n")

    def show(title, ks):
        print("\n%s: %d" % (title, len(ks)))
        for k in ks:
            ca, cb = fo.get(k, set()), fn.get(k, set())
            gained, lost = sorted(cb - ca), sorted(ca - cb)
            print("  %-22s %-34s %s%s" % (k[0], k[1], ("now fails " + "+".join(gained) + " ") if gained else "",
                                          ("fixed " + "+".join(lost)) if lost else ""))
    show("FAIL -> PASS", fixed)
    show("PASS -> FAIL (regressions)", broke)
    show("still failing, checks changed", changed)
    print("\nfailing styles per check (%s -> %s, compared styles only):" % (old, new))
    for c in CHECKS:
        a = sum(1 for k in keys if c in fo.get(k, ()))
        b = sum(1 for k in keys if c in fn.get(k, ()))
        print("  %-13s %3d -> %3d" % (c, a, b))
    pa = sum(1 for k in keys if so.get(k, ("", ""))[1] == "PASS")
    pb = sum(1 for k in keys if sn[k][1] == "PASS")
    print("\nfunctional PASS: %d -> %d of %d styles; written %s" % (pa, pb, len(keys), out))


if __name__ == "__main__":
    main()
