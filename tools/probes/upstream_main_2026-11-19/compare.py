#!/usr/bin/env python3
"""Question answered: for each backlog family a sweep re-landed (sweep.sh), how does the new
verdict compare with its ledger entry? Hinting is set aside: land.py applies a release's own
hinting only on the opt-in route (HINTING_EXTRACT), which waits for gftools-rust#2, so it fails
for every instructed family whatever the converter.

Classes: ERROR (no verdict), BUILD FAILS, HINTING-ONLY (0 table rows, no failing check but
hinting: lands CLEAN once hinting is applied), BETTER, SAME, WORSE (fewer / same / more table
rows or failing checks).

Usage: compare.py <sweep scratch dir>/results.tsv
"""
import re
import sys

STYLE = re.compile(r"(\S+)=(\d+|BUILD) functional=(PASS|-|FAIL\(([^)]*)\))")


def parse(detail):
    return [(style, rows, set(fails.split("+")) - {"hinting"} if fails else set())
            for style, rows, _, fails in STYLE.findall(detail)]


def summary(styles):
    return "; ".join("%s=%s %s" % (s, r, "+".join(sorted(f)) or "ok") for s, r, f in styles)


def classify(old, new):
    if not new:
        return "ERROR"
    if any(r == "BUILD" for _, r, _ in new):
        return "BUILD FAILS"
    if all(r == "0" and not f for _, r, f in new):
        return "HINTING-ONLY"
    rows = lambda x: sum(int(r) for _, r, _ in x if r.isdigit())
    fails = lambda x: set().union(*[f for _, _, f in x]) if x else set()
    if any(r == "BUILD" for _, r, _ in old):
        return "BETTER"
    o, n, of, nf = rows(old), rows(new), fails(old), fails(new)
    if (n < o and nf <= of) or (n <= o and nf < of):
        return "BETTER"
    if n > o or nf - of:
        return "WORSE"
    return "SAME"


def main():
    order = ["HINTING-ONLY", "BETTER", "SAME", "WORSE", "BUILD FAILS", "ERROR"]
    out = {k: [] for k in order}
    for line in open(sys.argv[1]):
        table, repo, _, old, new = line.rstrip("\n").split("\t")
        o, n = parse(old), parse(new)
        out[classify(o, n)].append("  %-22s old: %s\n  %-22s new: %s" % (
            repo, summary(o)[:140] or "-", "", summary(n)[:140] or new[:140]))
    for k in order:
        print("== %s: %d" % (k, len(out[k])))
        for x in out[k]:
            print(x)


if __name__ == "__main__":
    main()
