#!/usr/bin/env python3
"""Question: per family, how did the local crater run of the 21 overrides changed by
google/fonts #11277 and #11303 go? Counts per mode: identical / diff / which compiler failed,
and the most common last error line of each failing compiler.

Usage: crater_local_tally.py <crater results json>
"""
import collections, json, re, sys
d = json.load(open(sys.argv[1]))
fam = lambda tid: re.search(r"ofl/([^/]+)/config", tid).group(1)
mode = lambda tid: "gftools" if "(gftools" in tid else "default"
tally = collections.defaultdict(collections.Counter); errs = collections.defaultdict(collections.Counter)
for tid, v in d["success"].items():
    tally[fam(tid)][mode(tid) + (":identical" if v == "identical" else ":diff")] += 1
for tid, v in d["failure"].items():
    cf = v.get("compile_failed") if isinstance(v, dict) else None
    if not cf:
        tally[fam(tid)][mode(tid) + ":other"] += 1; continue
    tally[fam(tid)]["%s:fail(%s)" % (mode(tid), "+".join(sorted(cf)))] += 1
    for side, x in cf.items():
        lines = [l.strip() for l in x.get("stderr", "").splitlines() if re.search(r"rror", l) and "ninja" not in l and "Command failed" not in l]
        if lines:
            errs[fam(tid)][side + ": " + re.sub(r"\x1b\[[0-9;]*m|^\[[^\]]*\]\s*", "", lines[-1])[:150]] += 1
for f in sorted(tally):
    print("%-22s %s" % (f, "  ".join("%s=%d" % kv for kv in sorted(tally[f].items()))))
    for e, n in errs[f].most_common(2):
        print("      %dx %s" % (n, e))
