#!/usr/bin/env python3
"""Question: over several local crater runs (tools/crater_local.sh) taken together, how many
targets are identical / differ / fail in which compiler, and how many fontc-only failures are
static instances at no master's location? A family present in a later file replaces its
results from the earlier ones (re-pinned entries).

Usage: crater_local_union.py [--skipped <fontc_crater results/skipped.json>] <results json, oldest first>...
With --skipped, targets of the configs that file lists are left out, as crater's CI does.
"""
import collections, json, re, sys

def load(path):
    d = json.load(open(path)); out = {}
    for tid, v in d["success"].items():
        out[tid] = ("identical" if v == "identical" else "differ", False)
    for tid, v in d["failure"].items():
        cf = v.get("compile_failed") if isinstance(v, dict) else None
        err = re.sub(r"\x1b\[[0-9;]*m", "", cf["fontc"].get("stderr", "")) if cf and "fontc" in cf else ""
        off = sorted(cf or []) == ["fontc"] and ("not at the location of a master" in err or "is on no source" in err)
        out[tid] = ("fail " + "+".join(sorted(cf)) if cf else "other", off)
    return out

def family(tid):
    m = re.search(r"ofl/([^/]+)/config", tid)
    return m.group(1) if m else tid.split("/")[1]

args = sys.argv[1:]; skip = set()
if args[0] == "--skipped":
    skip = {k for g in json.load(open(args[1])) for k in g["configs"]}; args = args[2:]
merged = {}
for path in args:
    run = load(path); fams = {family(t) for t in run}
    merged = {t: v for t, v in merged.items() if family(t) not in fams}
    merged.update(run)
n_all = len(merged)
merged = {t: v for t, v in merged.items() if t.split(" ")[0] not in skip}
if skip:
    print("%d targets left out as skipped" % (n_all - len(merged)))
count = collections.Counter(); off = 0
for tid, (kind, is_off) in merged.items():
    mode = "gftools" if "(gftools" in tid else "default"
    count[(mode, kind)] += 1; off += is_off and mode == "gftools"
print("%d entries, %d targets" % (len({family(t) for t in merged}), len(merged)))
for (mode, kind), n in sorted(count.items()):
    print("%-8s %-22s %d" % (mode, kind, n))
print("gftools-mode fontc-only failures at no master's location: %d" % off)
