#!/usr/bin/env python3
"""Does a fontc_crater CI run agree with our local crater_local.sh run on the targets we added?
usage: python3 tools/crater_ci_compare.py <ci results json> <prev ci results json> <local summary.txt>...
Prints per-target mismatches, the totals, and existing targets whose category changed."""
import json, sys
def cat_ci(d):
    m = {t: ("same" if v == "identical" else "diff") for t, v in d.get("success", {}).items()}
    m.update({t: "FAIL" for t in d.get("failure", {})})
    return m
ci = cat_ci(json.load(open(sys.argv[1])))
prev = cat_ci(json.load(open(sys.argv[2])))
local = {}
for p in sys.argv[3:]:
    for l in open(p):
        k, _, t = l.rstrip("\n").partition("  ")
        if k in ("same", "diff", "FAIL"):
            local[t] = k
n = {"same": 0, "diff": 0, "FAIL": 0, "missing": 0}
for t, k in sorted(local.items()):
    c = ci.get(t, "missing")
    n[c] += 1
    if c != k:
        print("MISMATCH local=%s ci=%s %s" % (k, c, t))
print("local targets %d; in CI: %s" % (len(local), n))
moved = [(t, prev[t], ci[t]) for t in prev if t in ci and t not in local and prev[t] != ci[t]]
for t, a, b in moved:
    print("existing target changed: %s -> %s %s" % (a, b, t))
print("existing targets compared %d, changed %d" % (sum(1 for t in prev if t in ci and t not in local), len(moved)))
