#!/usr/bin/env python3
"""Does a hinted build pass the whole functional gate, not only `hinting`? Runs
functional_gate.run (all eight checks) on each <release.ttf> <built.ttf> pair and prints the
failing checks with their first failure.

Usage: full_gate.py <release.ttf> <built.ttf> [<release.ttf> <built.ttf>...]
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import functional_gate as fg  # noqa: E402

args = sys.argv[1:]
for release, built in zip(args[::2], args[1::2]):
    stem = os.path.splitext(os.path.basename(release))[0]
    res = fg.run(release, built, stem)
    failed = fg.failed_checks(res)
    detail = "; ".join("%s: %s" % (n, res["checks"][n]["failures"][0][:90]) for n in failed)
    print("%-26s %s%s" % (stem, "PASS all eight" if not failed else "FAIL " + ",".join(failed),
                          "  " + detail if detail else ""), flush=True)
