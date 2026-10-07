#!/usr/bin/env python3
"""Question answered: what does moving fontc_crater's gftools pin change for existing targets?

Compares two crater results files from runs on the same targets with the same fontc and
everything else equal except gftools: per target, success/failure in each run, and for
targets that succeed in both, whether the per-table fontc-vs-fontmake diff scores ttx_diff
reports moved (fontc pins gftools "to ensure ttx-diff output is stable").

Usage: compare.py <results before.json> <results after.json>
"""
import json
import re
import sys


def load(path):
    d = json.load(open(path))
    return d.get("success", {}), d.get("failure", {})


def mode(target):
    m = re.search(r"\((\w+)\)\s*$", target)
    return m.group(1) if m else "?"


NOISE = [(re.compile(r"\x1b\[[0-9;]*m"), ""),                      # ANSI colours
         (re.compile(r"\[?\d{4}-\d\d-\d\dT[\d:.]+Z?\]?"), "<time>"),
         (re.compile(r"ThreadId\(\d+\)"), "ThreadId"),
         (re.compile(r"/\S*/(?:tmp|\.tmp)\w*/?\S*"), "<path>"),
         (re.compile(r"/home/\S+"), "<path>")]
INFORMATIVE = re.compile(r"Error|Exception|error:|ERROR|produced|unknown|Invalid|must ")


def normalise(line):
    for pat, rep in NOISE:
        line = pat.sub(rep, line)
    return re.sub(r"\s+", " ", line).strip()


def last_error(failure):
    """Per compiler, the last stderr line that names an error (else the last line)."""
    errs = set()
    for r in (failure.get("compile_failed") or {}).values():
        lines = [normalise(l) for l in (r.get("stderr") or "").strip().splitlines() if l.strip()]
        named = [l for l in lines if INFORMATIVE.search(l)]
        errs.add((named or lines or ["?"])[-1][:110])
    return " / ".join(sorted(errs)) or normalise(json.dumps(failure))[:110]


def main():
    ok_a, bad_a = load(sys.argv[1])
    ok_b, bad_b = load(sys.argv[2])
    targets = sorted(set(ok_a) | set(bad_a) | set(ok_b) | set(bad_b))
    rows = {"same ok": 0, "same fail": 0}
    changes = []
    for t in targets:
        a = "ok" if t in ok_a else "FAIL" if t in bad_a else "-"
        b = "ok" if t in ok_b else "FAIL" if t in bad_b else "-"
        if a == b == "ok":
            if json.dumps(ok_a[t], sort_keys=True) == json.dumps(ok_b[t], sort_keys=True):
                rows["same ok"] += 1
            else:
                changes.append("diff scores moved  %s\n      before %s\n      after  %s"
                               % (t, json.dumps(ok_a[t], sort_keys=True)[:200],
                                  json.dumps(ok_b[t], sort_keys=True)[:200]))
        elif a == b == "FAIL":
            ea, eb = last_error(bad_a[t]), last_error(bad_b[t])
            if ea == eb:
                rows["same fail"] += 1
            else:
                changes.append("fails differently  %s\n      before %s\n      after  %s" % (t, ea, eb))
        else:
            why = last_error(bad_a[t]) if a == "FAIL" else last_error(bad_b[t]) if b == "FAIL" else ""
            changes.append("%-4s -> %-4s        %s%s" % (a, b, t, ("\n      " + why) if why else ""))
    print("%d targets (%s): unchanged ok %d, unchanged failure %d, changed %d"
          % (len(targets), ", ".join("%s %d" % (m, sum(mode(t) == m for t in targets))
                                     for m in ("default", "gftools")),
             rows["same ok"], rows["same fail"], len(changes)))
    for c in changes:
        print(c)


if __name__ == "__main__":
    main()
