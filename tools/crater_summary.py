#!/usr/bin/env python3
"""Summarise fontc_crater results files: one line per target, then totals.

Each target is "same" (fontc and fontmake output identical), "diff" (both built, the
outputs differ; the per-table scores follow) or "FAIL". Several files (a run made in
parts) are summarised together. Exit status 1 when any target failed.

    python3 tools/crater_summary.py <out>/2026-...json [more.json ...]
"""
import json
import os
import sys

same, diff, fail = [], [], []
for path in sys.argv[1:]:
    d = json.load(open(path))
    for t, v in d.get("success", {}).items():
        (same if v == "identical" else diff).append((t, v))
    fail.extend(d.get("failure", {}).items())
for t, _ in sorted(same):
    print("same  %s" % t)
for t, v in sorted(diff):
    print("diff  %s\n      %s" % (t, json.dumps(v.get("diffs", v))))
for t, why in sorted(fail):
    print("FAIL  %s\n      %s" % (t, json.dumps(why)[:300]))
print("%d targets: %d built (%d same, %d differ), %d failed (%s)" % (
    len(same) + len(diff) + len(fail), len(same) + len(diff), len(same), len(diff),
    len(fail), " ".join(os.path.basename(p) for p in sys.argv[1:])))
sys.exit(1 if fail else 0)
