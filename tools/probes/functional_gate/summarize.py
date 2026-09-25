#!/usr/bin/env python3
"""Question answered: across validate.py's run, how many styles fail each functional check,
and for which reasons?

Reads RESULT.tsv (validate.py's output) and the per-style verdict JSON it left in
$FG_SCRATCH/runs/<style>.json; counts styles per check and per failure class (the failure
message with numbers and names stripped to its kind), and lists the styles of each class.

Usage: $PY tools/probes/functional_gate/summarize.py tools/probes/functional_gate/RESULT.tsv > tools/probes/functional_gate/SUMMARY.txt
"""
import collections
import csv
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", ".."))
import functional_gate  # noqa: E402

CHECKS = ["cmap", "shaping", "rendering", "names", "line_spacing", "advances", "gdef"]


def kind(check, msg):
    m = msg
    if check == "names":
        g = re.match(r"(name ID \d+)|(OS/2\.\w+)", m)
        return g.group(0) if g else m[:40]
    if check == "shaping":
        g = re.match(r"(default features, [\w+ ]+?):|(G(SUB|POS) \w+ (on|off))|(language system \S+)", m)
        return g.group(0).rstrip(":") if g else m[:40]
    if check == "rendering":
        if m.startswith("diffenator3: ") and "encoded glyph" in m:
            return "diffenator3 glyph diffs"
        if m.startswith("diffenator3: ") and "word" in m:
            return "diffenator3 word diffs"
        if "draw ink more than rounding apart" in m:
            return "outline geometry (FreeType, 8 units/px)" + (": .notdef only" if re.search(r"\): \.notdef \d+px$", m) else "")
        return m[:40]
    if check == "line_spacing":
        return re.sub(r"[:(].*", "", m).strip()
    if check == "advances":
        return re.sub(r"\d+ ", "", re.sub(r":.*", "", m)).strip()
    if check == "gdef":
        return re.sub(r"\d+ ", "", re.sub(r"[:;(].*", "", m)).strip()
    return re.sub(r"\d+", "N", m)[:60]


def main():
    rows = list(csv.DictReader(open(sys.argv[1]), delimiter="\t"))
    verdicts = collections.Counter(r["verdict"] for r in rows)
    print("%d styles: %s" % (len(rows), dict(verdicts)))
    print("PASS: %s" % ", ".join(r["style"] for r in rows if r["verdict"] == "PASS"))
    print()
    for c in CHECKS:
        failing = [r["style"] for r in rows if r[c] not in ("PASS", "-")]
        print("%-12s fails in %d of %d styles" % (c, len(failing), len(rows)))
        classes = collections.defaultdict(list)
        for r in rows:
            if r[c] in ("PASS", "-"):
                continue
            j = os.path.join(functional_gate.SCRATCH, "runs", r["style"] + ".json")
            if not os.path.exists(j):
                continue
            for msg in json.load(open(j))["checks"][c]["failures"]:
                k = kind(c, msg)
                if r["style"] not in classes[k]:
                    classes[k].append(r["style"])
        for k, sts in sorted(classes.items(), key=lambda kv: -len(kv[1])):
            print("    %3d  %s: %s" % (len(sts), k, ", ".join(sts)))
    print()


if __name__ == "__main__":
    main()
