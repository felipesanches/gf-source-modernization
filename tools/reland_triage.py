#!/usr/bin/env python3
"""Question answered: after a re-land run, which styles fail which functional-gate checks,
for which recurring cause -- so follow-up work can be ranked by how many styles it fixes.

Reads logs/reland-<tag>/<repo>.log (tools/land.py output: the verdict line, then the
functional gate's summary per failing style, in style order) and writes
logs/reland-<tag>/triage.tsv (one row per style and failing check, with a cause class and
the gate's first detail line) and prints counts per check and per cause.

Usage: reland_triage.py <tag>
"""
import collections
import glob
import os
import re
import sys

W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHECKS = ("cmap", "shaping", "rendering", "names", "line_spacing", "advances", "gdef")


def cause(check, details):
    """A coarse, rule-based class for one failing check from its detail lines."""
    text = " ".join(details)
    if check == "names":
        ids = sorted(set(re.findall(r"name ID (\d+)", text)), key=int)
        return "names: ID " + "+".join(ids) if ids else "names: other"
    if check == "line_spacing":
        if "USE_TYPO_METRICS set by the build" in text:
            return "line_spacing: USE_TYPO_METRICS set by build"
        return "line_spacing: metrics differ"
    if check == "rendering":
        if re.search(r"\.notdef", text):
            return "rendering: .notdef"
        return "rendering: outlines differ"
    if check == "shaping":
        kinds = [m.group(1) for d in details
                 for m in [re.match(r"^(?:default features, )?([^:]+): \d+ of \d+ runs differ", d)] if m]
        return "shaping: " + (kinds[0] if kinds else "other")
    if check == "gdef":
        return "gdef: classes differ"
    if check == "advances":
        return "advances: differ"
    if check == "cmap":
        return "cmap: differs"
    return check


def parse(log):
    lines = open(log, encoding="utf-8", errors="replace").read().splitlines()
    if not lines:
        return []
    head = lines[0]
    m = re.match(r"^(\S+): (\S+) @ \S+, \d+ commits, (\d+) edit\(s\): (.*)$", head)
    if not m:
        return [{"repo": os.path.basename(log)[:-4], "style": "-", "check": "LANDING",
                 "cause": "landing failed", "detail": (lines[-1] if lines else "")[:200]}]
    repo, status, _edits, summary = m.groups()
    styles = []
    for part in summary.split("; "):
        sm = re.match(r"^(\S+)=(\S+) functional=(\S+)$", part)
        if sm:
            styles.append(sm.groups())
    # detail blocks: one per style whose functional verdict is not PASS, in order;
    # each block is the 7 check lines (5-space indent) with their 9-space detail lines
    blocks, cur = [], None
    for l in lines[1:]:
        cm = re.match(r"^     (\w+)\s+(PASS|FAIL)\b(.*)$", l)
        if cm and cm.group(1) in CHECKS:
            if cm.group(1) == "cmap":
                cur = {}
                blocks.append(cur)
            if cur is not None:
                cur[cm.group(1)] = {"status": cm.group(2), "summary": cm.group(3).strip(), "details": []}
                last = cm.group(1)
        elif cur is not None and l.startswith("         - "):
            cur[last]["details"].append(l.strip()[2:])
    rows = []
    failing = [s for s in styles if s[2] != "PASS"]
    for (style, table, fverdict), block in zip(failing, blocks):
        for check in CHECKS:
            c = block.get(check)
            if c and c["status"] == "FAIL":
                rows.append({"repo": repo, "style": style, "check": check,
                             "cause": cause(check, c["details"]),
                             "detail": (c["details"][0] if c["details"] else c["summary"])[:200]})
    for style, table, fverdict in styles:
        if fverdict == "PASS" and table not in ("0",):
            rows.append({"repo": repo, "style": style, "check": "table_gate",
                         "cause": "table gate rows (functional PASS)", "detail": table})
        if fverdict == "-":
            rows.append({"repo": repo, "style": style, "check": "BUILD", "cause": "not built",
                         "detail": table})
    return rows, [(repo, st, t, f) for st, t, f in styles]


def main():
    tag = sys.argv[1]
    d = os.path.join(W, "logs", "reland-" + tag)
    all_rows, all_styles = [], []
    for log in sorted(glob.glob(os.path.join(d, "*.log"))):
        r = parse(log)
        if isinstance(r, tuple):
            all_rows += r[0]
            all_styles += r[1]
        else:
            all_rows += r
    with open(os.path.join(d, "triage.tsv"), "w") as fh:
        fh.write("repo\tstyle\tcheck\tcause\tdetail\n")
        for r in all_rows:
            fh.write("\t".join([r["repo"], r["style"], r["check"], r["cause"], r["detail"].replace("\t", " ")]) + "\n")
    passed = sum(1 for _, _, t, f in all_styles if f == "PASS")
    clean = sum(1 for _, _, t, f in all_styles if f == "PASS" and t == "0")
    print("styles: %d; functional PASS %d; CLEAN (table 0 + functional PASS) %d" % (len(all_styles), passed, clean))
    by_check = collections.Counter((r["check"]) for r in all_rows)
    styles_by_cause = collections.defaultdict(set)
    for r in all_rows:
        styles_by_cause[r["cause"]].add((r["repo"], r["style"]))
    print("\nfailing styles per check:")
    for k, n in by_check.most_common():
        print("  %-14s %d" % (k, n))
    print("\nfailing styles per cause:")
    for k, v in sorted(styles_by_cause.items(), key=lambda kv: -len(kv[1])):
        print("  %4d  %s" % (len(v), k))
    # how many styles would pass if only one cause were fixed
    fails = collections.defaultdict(set)
    for r in all_rows:
        fails[(r["repo"], r["style"])].add(r["cause"])
    only = collections.Counter(next(iter(c)) for c in fails.values() if len(c) == 1)
    print("\nstyles failing on exactly one cause (fixing it alone makes them pass):")
    for k, n in only.most_common():
        print("  %4d  %s" % (n, k))


if __name__ == "__main__":
    main()
